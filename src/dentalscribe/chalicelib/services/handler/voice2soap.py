import json
import logging
from chalicelib.utils.time_util import TimeUtil
from chalicelib.clients.aws.bedrock import BedrockClient
from chalicelib.clients.aws.s3 import S3Client
from chalicelib.clients.aws.transcribe import TranscribeClient
from chalicelib.prompts.factory import PromptFactory
from chalicelib.prompts.schemas.voice2soap import Voice2SoapSchema
from chalicelib.models.job import Job
from chalicelib.constants import (
    TRANSCRIBE_DESTINATION_FILENAME,
    TRANSCRIPTION_DESTINATION_KEY_PREFIX,
    BEDROCK_JSON_DELIMITER,
)
from chalicelib.config import Config
from chalicelib.enums.job import JobStatus, JobType
from chalicelib.repositories.job import JobRepository

logger = logging.getLogger(__name__)

class Voice2SoapJobHandler:
    def __init__(self):
        self.aws_config = Config.get_aws_config()
        self.bedrock_client = BedrockClient()
        self.s3_client = S3Client()
        self.transcribe_client = TranscribeClient()
        self.job_repository = JobRepository()

    def start_transcription(self, job: Job):
        """音声ファイルの文字起こしを開始"""
        logger.info("Starting transcription for job_id: %s", job.job_id)

        job_name = job.job_id
        payload = json.loads(job.payload)
        source_s3_key = payload.get("source_s3_key")
        media_uri = f"s3://{self.aws_config['S3_BUCKET']}/{source_s3_key}"
        output_bucket = self.aws_config['S3_BUCKET']
        output_key = f"{TRANSCRIPTION_DESTINATION_KEY_PREFIX}{job_name}/{TRANSCRIBE_DESTINATION_FILENAME}"

        self.transcribe_client.start_transcription_job(
            job_name=job_name,
            media_uri=media_uri,
            output_bucket=output_bucket,
            output_key=output_key
        )


    def generate_soap(self, job: Job):
        """Transcribe結果からSOAP形式のデータを生成"""
        payload = json.loads(job.payload)
        source_s3_key = payload.get("source_s3_key")

        logger.info("Generating SOAP for source_s3_key: %s", source_s3_key)

        try:
            # TranscribeのJSON結果を取得
            bucket = self.aws_config['S3_BUCKET']
            transcribe_result = self.s3_client.get_json_object(bucket, source_s3_key)
            
            # TranscriptからテキストとConfidenceを抽出
            results = transcribe_result.get('results', {})
            transcripts = results.get('transcripts', [])
            
            if not transcripts:
                raise ValueError("No transcription results found")
            
            transcription_text = transcripts[0].get('transcript', '')
            
            if not transcription_text.strip():
                raise ValueError("Empty transcription text")
                
            logger.info("Transcription text extracted, length: %d", len(transcription_text))
            
            # BedrockでSOAP形式に変換
            soap_data = self._generate_soap_with_bedrock(transcription_text)
            
            # ジョブ結果を更新
            job.result = json.dumps(soap_data)
            job.job_status = JobStatus.COMPLETED
            job.updated_at = TimeUtil.now_str()
            job.save()

            # 親ジョブを更新
            parent_job = self.job_repository.find(job.parent_job_id)
            if parent_job:
                parent_job.completed_child_jobs += 1
                parent_job.job_status = JobStatus.COMPLETED
                parent_job.updated_at = TimeUtil.now_str()
                parent_job.result = json.dumps({
                    "transcription_text": transcription_text,
                    "soap_data": soap_data
                })
                parent_job.save()
                
            logger.info("SOAP generation completed for job: %s", job.job_id)
            
        except Exception as e:
            logger.error("Failed to generate SOAP for job %s: %s", job.job_id, e)
            job.job_status = JobStatus.FAILED
            job.error = str(e)
            job.updated_at = TimeUtil.now_str()
            job.save()
            raise

    def _generate_soap_with_bedrock(self, transcription_text: str) -> dict:
        """BedrockとClaude APIを使用してTranscriptionテキストからSOAP形式のデータを生成"""
        logger.info("Generating SOAP from transcription text, length: %d", len(transcription_text))
        
        try:
            # ファクトリーでプロンプトを生成
            prompt_text = PromptFactory.create_voice2soap_prompt(transcription_text)
            
            logger.info("Generated prompt for Bedrock using factory")
            
            # Bedrockで生成
            context = [prompt_text]
            generated_text, input_tokens, output_tokens = self.bedrock_client.generate_text(
                context=context,
                max_tokens=4096,
                temperature=0.1,  # SOAP形式なので一貫性を重視
                top_p=0.9
            )
            
            logger.info("Bedrock generation completed. Input tokens: %d, Output tokens: %d", 
                       input_tokens, output_tokens)
            
            # 生成されたテキストからJSON部分を抽出
            try:
                json_content = self._extract_json_from_response(generated_text)
                soap_data = json.loads(json_content)
                
                # スキーマ検証
                schema_instance = Voice2SoapSchema()
                schema_instance.validate(soap_data)
                
                logger.info("SOAP data generated successfully")
                return soap_data
                
            except json.JSONDecodeError as e:
                logger.error("Failed to parse extracted JSON: %s", e)
                logger.error("Extracted JSON: %s", json_content if 'json_content' in locals() else 'N/A')
                logger.error("Full generated text: %s", generated_text)
                raise ValueError(f"Invalid JSON generated by Bedrock: {e}")
            
        except Exception as e:
            logger.error("Failed to generate SOAP data: %s", e)
            raise

    def _extract_json_from_response(self, response_text: str) -> str:
        """Bedrockの応答からJSON部分を抽出"""
        try:
            # デリミターで囲まれた部分を検索
            delimiter_count = response_text.count(BEDROCK_JSON_DELIMITER)
            
            if delimiter_count >= 2:
                # 最初と最後のデリミターの位置を取得
                start_idx = response_text.find(BEDROCK_JSON_DELIMITER) + len(BEDROCK_JSON_DELIMITER)
                end_idx = response_text.rfind(BEDROCK_JSON_DELIMITER)
                
                if start_idx < end_idx:
                    json_content = response_text[start_idx:end_idx].strip()
                    logger.info("Extracted JSON content using delimiter")
                    return json_content
                    
            logger.warning("Delimiter not found or malformed, attempting fallback JSON extraction")
            
            # フォールバック: 最初の{から最後の}までを抽出
            start_brace = response_text.find('{')
            end_brace = response_text.rfind('}')
            
            if start_brace != -1 and end_brace != -1 and start_brace < end_brace:
                json_content = response_text[start_brace:end_brace + 1]
                logger.info("Extracted JSON content using brace fallback")
                return json_content
            
            raise ValueError("No valid JSON structure found in response")
            
        except Exception as e:
            logger.error("Failed to extract JSON from response: %s", e)
            raise ValueError(f"JSON extraction failed: {e}")