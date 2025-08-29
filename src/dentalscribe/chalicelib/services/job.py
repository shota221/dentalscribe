import json
import uuid
import logging
import os
from chalicelib.clients.aws.s3 import S3Client
from chalicelib.clients.aws.sqs import SQSClient
from chalicelib.clients.aws.transcribe import TranscribeClient
from chalicelib.clients.aws.bedrock import BedrockClient
from chalicelib.services.handler.voice2soap import Voice2SoapJobHandler
from typing import List, Dict, Any, Generator, Optional, Tuple, Iterator
from chalicelib.utils.decorators import result_handler
from chalicelib.utils.time_util import TimeUtil
from chalicelib.config import Config
from chalicelib.exceptions import ValidationError
from chalicelib.responses.get_voice2soap_job import SoapData
from chalicelib.responses import GetVoice2SoapJobResponse, CreateVoice2SoapJobResponse
from chalicelib.models.job import Job
from chalicelib.enums.job import JobStatus, JobType
from chalicelib.repositories.job import JobRepository
from chalicelib.constants import (
    TRANSCRIPTION_SOURCE_KEY_PREFIX,
    TRANSCRIPTION_DESTINATION_KEY_PREFIX,
    TRANSCRIBE_DESTINATION_FILENAME,
    PARENT_JOB_ID_NONE
)

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self):
        self.s3_client = S3Client()
        self.sqs_client = SQSClient()
        self.transcribe_client = TranscribeClient()
        self.bedrock_client = BedrockClient()
        self.voice2soap_job_handler = Voice2SoapJobHandler()
        self.aws_config = Config.get_aws_config()
        self.job_repository = JobRepository()

    @result_handler
    def get_voice2soap_job(self, job_id: str) -> GetVoice2SoapJobResponse:
        job = self.job_repository.find(job_id)
        
        if not job:
            raise ValidationError("Job not found")
        
        if job.job_type != JobType.VOICE_TO_SOAP:
            raise ValidationError("Job is not a voice2soap job")

        # 基本的なステータス情報
        response_data = {
            "job_id": job.job_id,
            "status": job.job_status.value.lower(),
            "transcription_text": "",
            "soap_data": None
        }

        # ジョブが完了している場合、結果を返す
        if job.job_status == JobStatus.COMPLETED and job.result:
            try:
                result_data = json.loads(job.result)
                response_data["transcription_text"] = result_data.get("transcription_text", "")
                
                soap_data_raw = result_data.get("soap_data", {})
                if soap_data_raw:
                    response_data["soap_data"] = SoapData(
                        subjective=soap_data_raw.get("subjective", ""),
                        objective=soap_data_raw.get("objective", ""),
                        assessment=soap_data_raw.get("assessment", ""),
                        plan=soap_data_raw.get("plan", "")
                    )
            except json.JSONDecodeError:
                logger.warning("Failed to parse job result for job %s", job_id)

        return GetVoice2SoapJobResponse(**response_data)

    @result_handler
    def create_voice2soap_job(self, json_body: Dict[str, Any]) -> CreateVoice2SoapJobResponse:
        # リクエストデータの検証
            
        if json_body.get('source_s3_key'):
            source_s3_key = json_body['source_s3_key']
        elif json_body.get('upload_id'):
            # S3からupload_idで始まるファイルを検索
            upload_id = json_body['upload_id']
            prefix = f"{TRANSCRIPTION_SOURCE_KEY_PREFIX}{upload_id}"
            
            # S3バケットからプレフィックスにマッチするオブジェクトを取得
            bucket = self.aws_config['S3_BUCKET']
            objects = self.s3_client.list_objects(bucket, prefix)
            
            if not objects:
                raise ValidationError(f"No files found with upload_id prefix: {upload_id}")
            
            # 最初に見つかったファイルを使用
            source_s3_key = objects[0]['Key']
            logger.info("Found file for upload_id %s: %s", upload_id, source_s3_key)
        else:
            raise ValidationError("Either 'upload_id' or 'source_s3_key' must be provided")

        logger.info("Creating voice2soap job for S3 key: %s", source_s3_key)

        # 親ジョブ（VOICE_TO_SOAP）を作成
        parent_job = Job(
            job_type=JobType.VOICE_TO_SOAP,
            job_status=JobStatus.IN_PROGRESS,
            total_child_jobs=2,  # TRANSCRIBE + GENERATE_SOAP
            completed_child_jobs=0,
            failed_child_jobs=0,
            payload=json.dumps({"source_s3_key": source_s3_key}),
            created_at=TimeUtil.now_str(),
            updated_at=TimeUtil.now_str()
        )
        parent_job.save()

        logger.info("Created parent job: %s", parent_job.job_id)

        # 子ジョブ（TRANSCRIBE）を作成
        transcribe_job = Job(
            job_type=JobType.TRANSCRIBE,
            job_status=JobStatus.PENDING,
            parent_job_id=parent_job.job_id,
            payload=json.dumps({
                "source_s3_key": source_s3_key,
                "parent_job_id": parent_job.job_id
            }),
            created_at=TimeUtil.now_str(),
            updated_at=TimeUtil.now_str()
        )
        transcribe_job.save()

        logger.info("Created transcribe child job: %s", transcribe_job.job_id)

        # SQSにメッセージを送信してTranscribeジョブを開始
        queue_name = self.aws_config["SQS_JOB_QUEUE"]
        message_body = json.dumps({
            "job_id": transcribe_job.job_id,
            "job_type": JobType.TRANSCRIBE.value,
            "parent_job_id": parent_job.job_id
        })
        
        self.sqs_client.send_message(queue_name, message_body)
        logger.info("Sent SQS message for transcribe job: %s", transcribe_job.job_id)

        return CreateVoice2SoapJobResponse(
            job_id=parent_job.job_id
        )

    @result_handler
    def complete_transcribe_job(self, transcribe_destination_key: str):
        key_parts = transcribe_destination_key.split('/')
        if len(key_parts) >= 3: 
            job_id = key_parts[2] 
        else:
            raise ValidationError("Invalid S3 key format")

        job = self.job_repository.find(job_id)

        if not job or job.job_type != JobType.TRANSCRIBE:
            raise ValidationError("Job not found")

        parent_job = self.job_repository.find(job.parent_job_id)

        job.job_status = JobStatus.COMPLETED

        if parent_job:
            parent_job.completed_child_jobs += 1
            parent_job.updated_at = TimeUtil.now_str()
            parent_job.save()
        job.save()

        generate_soap_job = Job(
            job_type=JobType.GENERATE_SOAP,
            job_status=JobStatus.PENDING,
            parent_job_id=parent_job.job_id,
            payload=json.dumps({
                "source_s3_key": transcribe_destination_key,
                "parent_job_id": parent_job.job_id
            }),
            created_at=TimeUtil.now_str(),
            updated_at=TimeUtil.now_str()
        )

        generate_soap_job.save()

        logger.info("Created generate SOAP job: %s", generate_soap_job.job_id)

        # SQSにメッセージを送信してTranscribeジョブを開始
        queue_name = self.aws_config["SQS_JOB_QUEUE"]
        message_body = json.dumps({
            "job_id": generate_soap_job.job_id,
            "job_type": JobType.GENERATE_SOAP.value,
            "parent_job_id": parent_job.job_id
        })
        
        self.sqs_client.send_message(queue_name, message_body)
        logger.info("Sent SQS message for generate SOAP job: %s", generate_soap_job.job_id)



    @result_handler
    def handle_sqs_message(self, json_body: Dict[str, Any]) -> None:
        job_id = json_body["job_id"]

        logger.info("Handling job: %s", job_id)

        job = self.job_repository.find(job_id)

        if not job:
            raise ValidationError("Job not found")

        job.job_status = JobStatus.IN_PROGRESS
        job.save()

        try:
            if job.job_type == JobType.TRANSCRIBE:
                self.voice2soap_job_handler.start_transcription(job)
            elif job.job_type == JobType.GENERATE_SOAP:
                self.voice2soap_job_handler.generate_soap(job)
            else:
                raise ValidationError("Job type not supported")
                        
        except Exception as e:
            job.result = None
            job.job_status = JobStatus.FAILED
            job.error = str(e)
            job.save()
            raise e


    @result_handler
    def handle_failed_sqs_message(self, json_body: Dict[str, Any]) -> None:
        job_id = json_body["job_id"]
        job = self.job_repository.find(job_id)

        if not job:
            raise ValidationError("Job not found")

        self.__handle_failed_job(job)

    def __handle_failed_job(self, job: Job) -> None:
        """失敗したジョブの処理"""
        logger.info("Handling failed job: %s", job.job_id)
        
        job.job_status = JobStatus.FAILED
        job.updated_at = TimeUtil.now_str()
        job.save()
        
        if job.parent_job_id and job.parent_job_id != PARENT_JOB_ID_NONE:
            logger.info("Updating parent job %s due to child job failure", job.parent_job_id)
            parent_job = self.job_repository.find(job.parent_job_id)
            parent_job.failed_child_jobs += 1
            parent_job.updated_at = TimeUtil.now_str()
            parent_job.job_status = JobStatus.FAILED
            parent_job.save()
            logger.info("Updated parent job %s as FAILED due to child job failure", parent_job.job_id)