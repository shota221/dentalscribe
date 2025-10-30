import json
import uuid
import logging
import os
import time
import random
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

        # 子ジョブ（Transcribeジョブ）の詳細を取得
        child_jobs = self.job_repository.find_by_parent_job_id(job_id, JobType.TRANSCRIBE)
        all_transcribe_finished = all(j.job_status in [JobStatus.COMPLETED, JobStatus.FAILED] for j in child_jobs) and len(child_jobs) > 0
        # parent_job_idがjob_idのGENERATE_SOAPジョブが存在するか
        generate_soap_jobs = self.job_repository.find_by_parent_job_id(job_id, JobType.GENERATE_SOAP)
        if all_transcribe_finished and not generate_soap_jobs:
            logger.info(f"All transcribe jobs finished (completed/failed) and no generate_soap job found for parent {job_id}. Starting SOAP generation.")
            self._start_soap_generation(job_id)

        # 基本的なステータス情報
        response_data = {
            "job_id": job.job_id,
            "status": job.job_status.value.lower(),
            "transcription_text": "",
            "soap_data": None,
            "child_jobs": []
        }

        # 子ジョブ（Transcribeジョブ）の詳細を取得
        child_jobs_info = []
        child_jobs = self.job_repository.find_by_parent_job_id(job_id, JobType.TRANSCRIBE)
        
        for child_job in child_jobs:
            child_job_detail = {
                "job_id": child_job.job_id,
                "upload_id": self._extract_upload_id_from_job(child_job),
                "status": child_job.job_status.value,
                "transcription_text": ""
            }
            
            # 完了したジョブの場合はTranscribeテキストも取得
            if child_job.job_status == JobStatus.COMPLETED:
                try:
                    transcription_text = self._get_transcription_text_from_job(child_job)
                    child_job_detail["transcription_text"] = transcription_text
                except Exception as e:
                    logger.warning("Failed to get transcription for job %s: %s", child_job.job_id, e)
            
            child_jobs_info.append(child_job_detail)

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

        from chalicelib.responses.get_voice2soap_job import ChildJobDetail
        response_data["child_jobs"] = [ChildJobDetail(**child) for child in child_jobs_info]

        return GetVoice2SoapJobResponse(**response_data)

    @result_handler
    def create_voice2soap_job(self, json_body: Dict[str, Any]) -> CreateVoice2SoapJobResponse:
        # リクエストデータの検証と正規化
        upload_ids = []
        
        # 新しい複数upload_idsフォーマット
        if json_body.get('upload_ids'):
            upload_ids = json_body['upload_ids']
        # 後方互換性のため単一upload_idもサポート
        elif json_body.get('upload_id'):
            upload_ids = [json_body['upload_id']]
        # 直接S3キー指定もサポート
        elif json_body.get('source_s3_key'):
            source_s3_key = json_body['source_s3_key']
            # 直接S3キー指定の場合は従来通りの処理
            return self._create_single_voice2soap_job(source_s3_key)
        else:
            raise ValidationError("Either 'upload_ids', 'upload_id' or 'source_s3_key' must be provided")

        if not upload_ids:
            raise ValidationError("upload_ids cannot be empty")

        logger.info("Creating voice2soap job for upload_ids: %s", upload_ids)

        # 各upload_idに対応するS3キーを取得し、Transcribe済みかチェック
        transcribe_jobs_info = []
        for upload_id in upload_ids:
            job_info = self._prepare_transcribe_job_for_upload_id(upload_id)
            transcribe_jobs_info.append(job_info)

        # 親ジョブ（VOICE_TO_SOAP）を作成
        total_transcribe_jobs = len([info for info in transcribe_jobs_info if info['needs_transcribe']])
        already_completed_jobs = len(transcribe_jobs_info) - total_transcribe_jobs
        total_expected_transcribe_jobs = len(transcribe_jobs_info)  # 全Transcribeジョブ数（既完了+新規）
        
        logger.info("Parent job creation: total_transcribe_jobs=%d, already_completed=%d, total_expected=%d, upload_ids=%s", 
                   total_transcribe_jobs, already_completed_jobs, total_expected_transcribe_jobs, upload_ids)
        
        parent_job = Job(
            job_type=JobType.VOICE_TO_SOAP,
            job_status=JobStatus.IN_PROGRESS,
            total_child_jobs=total_expected_transcribe_jobs,  # 実際のTranscribeジョブ総数
            completed_child_jobs=already_completed_jobs,  # 既に完了しているTranscribeジョブ数
            failed_child_jobs=0,
            payload=json.dumps({"upload_ids": upload_ids}),
            created_at=TimeUtil.now_str(),
            updated_at=TimeUtil.now_str()
        )
        parent_job.save()

        logger.info("Created parent job: %s with total_child_jobs=%d, completed_child_jobs=%d", 
                   parent_job.job_id, parent_job.total_child_jobs, parent_job.completed_child_jobs)

        # Transcribeが必要なジョブを作成・開始
        child_jobs = []
        for info in transcribe_jobs_info:
            if info['needs_transcribe']:
                # 子ジョブ（TRANSCRIBE）を作成
                transcribe_job = Job(
                    job_type=JobType.TRANSCRIBE,
                    job_status=JobStatus.PENDING,
                    parent_job_id=parent_job.job_id,
                    payload=json.dumps({
                        "source_s3_key": info['source_s3_key'],
                        "upload_id": info['upload_id'],
                        "parent_job_id": parent_job.job_id
                    }),
                    created_at=TimeUtil.now_str(),
                    updated_at=TimeUtil.now_str()
                )
                transcribe_job.save()

                # SQSにメッセージを送信してTranscribeジョブを開始
                queue_name = self.aws_config["SQS_JOB_QUEUE"]
                message_body = json.dumps({
                    "job_id": transcribe_job.job_id,
                    "job_type": JobType.TRANSCRIBE.value,
                    "parent_job_id": parent_job.job_id
                })
                
                self.sqs_client.send_message(queue_name, message_body)
                logger.info("Sent SQS message for transcribe job: %s", transcribe_job.job_id)
                
                child_jobs.append({
                    "job_id": transcribe_job.job_id,
                    "upload_id": info['upload_id'],
                    "status": "QUEUED",
                    "service": "transcribe"
                })
            else:
                # 既に完了している場合
                child_jobs.append({
                    "job_id": info['existing_job_id'] if info.get('existing_job_id') else f"completed-{info['upload_id']}",
                    "upload_id": info['upload_id'],
                    "status": "COMPLETED",
                    "service": "transcribe"
                })

        # すべてのTranscribeジョブが完了している場合は、即座にSOAP生成を開始
        if total_transcribe_jobs == 0:
            logger.info("All transcribe jobs already completed, starting SOAP generation immediately for parent: %s", parent_job.job_id)
            self._start_soap_generation(parent_job.job_id)

        from chalicelib.responses.create_voice2soap_job import ChildJobInfo
        child_job_infos = [ChildJobInfo(**job) for job in child_jobs]

        return CreateVoice2SoapJobResponse(
            job_id=parent_job.job_id,
            status="QUEUED",
            service="voice2soap",
            message="Voice to SOAP conversion job started",
            child_jobs=child_job_infos
        )

    @result_handler
    def complete_transcribe_job(self, transcribe_destination_key: str):
        key_parts = transcribe_destination_key.split('/')
        if len(key_parts) >= 3: 
            job_id = key_parts[2] 
        else:
            raise ValidationError("Invalid S3 key format")

        time.sleep(random.random())

        job = self.job_repository.find(job_id)

        if not job or job.job_type != JobType.TRANSCRIBE:
            raise ValidationError("Job not found")

        parent_job = self.job_repository.find(job.parent_job_id)

        job.job_status = JobStatus.COMPLETED
        job.completed_at = TimeUtil.now_str()
        job.save()

        if parent_job:
            parent_job.completed_child_jobs += 1
            parent_job.updated_at = TimeUtil.now_str()
            parent_job.save()  # 親ジョブを先に保存
            
            # 全てのTranscribeジョブが完了（成功・失敗問わず）したかチェック
            expected_transcribe_jobs = parent_job.total_child_jobs  # GENERATE_SOAPジョブは含まない
            total_finished_jobs = parent_job.completed_child_jobs + parent_job.failed_child_jobs
            
            logger.info("Transcribe job completion check for parent %s: expected=%d, completed=%d, failed=%d, total_finished=%d", 
                       parent_job.job_id, expected_transcribe_jobs, parent_job.completed_child_jobs, 
                       parent_job.failed_child_jobs, total_finished_jobs)
            
            if total_finished_jobs >= expected_transcribe_jobs:
                logger.info("All transcribe jobs finished (completed: %d, failed: %d) for parent: %s", 
                           parent_job.completed_child_jobs, parent_job.failed_child_jobs, parent_job.job_id)
                # SOAP生成開始判定のみ残す
                if parent_job.completed_child_jobs > 0:
                    logger.info("Starting SOAP generation with %d successful transcriptions", parent_job.completed_child_jobs)
                    self._start_soap_generation(parent_job.job_id)
                else:
                    logger.error("All transcribe jobs failed for parent: %s", parent_job.job_id)
                    parent_job.job_status = JobStatus.FAILED
                    parent_job.error = "All transcribe jobs failed"
                    parent_job.save()
            else:
                logger.info("Waiting for remaining transcribe jobs to complete for parent: %s (need %d more)", 
                           parent_job.job_id, expected_transcribe_jobs - total_finished_jobs)
                
                # デバッグ情報: 子ジョブの状態を詳しく確認
                child_jobs = self.job_repository.find_by_parent_job_id(parent_job.job_id, JobType.TRANSCRIBE)
                logger.info("Current child jobs for parent %s: total_found=%d", parent_job.job_id, len(child_jobs))
                for child_job in child_jobs:
                    logger.info("Child job %s: status=%s", child_job.job_id, child_job.job_status.value)

        logger.info("Completed transcribe job: %s", job.job_id)



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
            parent_job.save()  # 親ジョブを先に保存
            
            # Transcribeジョブの場合は、他の成功したジョブがあればSOAP生成を続行
            if job.job_type == JobType.TRANSCRIBE:
                expected_transcribe_jobs = parent_job.total_child_jobs  # GENERATE_SOAPジョブは含まない
                total_finished_jobs = parent_job.completed_child_jobs + parent_job.failed_child_jobs
                if total_finished_jobs >= expected_transcribe_jobs:
                    logger.info("All transcribe jobs finished (completed: %d, failed: %d) for parent: %s", 
                               parent_job.completed_child_jobs, parent_job.failed_child_jobs, parent_job.job_id)
                    # SOAP生成開始判定のみ残す
                    if parent_job.completed_child_jobs > 0:
                        logger.info("Starting SOAP generation with %d successful transcriptions (despite %d failures)", 
                                   parent_job.completed_child_jobs, parent_job.failed_child_jobs)
                        self._start_soap_generation(parent_job.job_id)
                    else:
                        logger.error("All transcribe jobs failed for parent: %s", parent_job.job_id)
                        parent_job.job_status = JobStatus.FAILED
                        parent_job.error = "All transcribe jobs failed"
                        parent_job.save()
                else:
                    logger.info("Waiting for remaining transcribe jobs to complete for parent: %s (need %d more)", 
                               parent_job.job_id, expected_transcribe_jobs - total_finished_jobs)
            else:
                # Transcribe以外のジョブが失敗した場合は従来通り親ジョブも失敗とする
                parent_job.job_status = JobStatus.FAILED
                parent_job.error = f"Child job {job.job_id} failed: {job.error}"
                parent_job.save()
            
            logger.info("Updated parent job %s status", parent_job.job_id)

    def _prepare_transcribe_job_for_upload_id(self, upload_id: str) -> Dict[str, Any]:
        """upload_idに対応するTranscribeジョブの情報を準備"""
        # S3からupload_idで始まるファイルを検索
        prefix = f"{TRANSCRIPTION_SOURCE_KEY_PREFIX}{upload_id}"
        bucket = self.aws_config['S3_BUCKET']
        objects = self.s3_client.list_objects(bucket, prefix)
        
        if not objects:
            raise ValidationError(f"No files found with upload_id prefix: {upload_id}")
        
        source_s3_key = objects[0]['Key']
        
        # Transcribe結果が既に存在するかチェック
        transcribe_result_key = f"{TRANSCRIPTION_DESTINATION_KEY_PREFIX}{upload_id}/{TRANSCRIBE_DESTINATION_FILENAME}"
        transcribe_result_exists = self.s3_client.exists(bucket, transcribe_result_key)
        
        return {
            "upload_id": upload_id,
            "source_s3_key": source_s3_key,
            "needs_transcribe": not transcribe_result_exists,
            "transcribe_result_key": transcribe_result_key if transcribe_result_exists else None
        }

    def _create_single_voice2soap_job(self, source_s3_key: str) -> CreateVoice2SoapJobResponse:
        """従来の単一ファイル処理（後方互換性のため）"""
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

        # SQSにメッセージを送信
        queue_name = self.aws_config["SQS_JOB_QUEUE"]
        message_body = json.dumps({
            "job_id": transcribe_job.job_id,
            "job_type": JobType.TRANSCRIBE.value,
            "parent_job_id": parent_job.job_id
        })
        
        self.sqs_client.send_message(queue_name, message_body)

        from chalicelib.responses.create_voice2soap_job import ChildJobInfo
        child_jobs = [ChildJobInfo(
            job_id=transcribe_job.job_id,
            upload_id="unknown",
            status="QUEUED",
            service="transcribe"
        )]

        return CreateVoice2SoapJobResponse(
            job_id=parent_job.job_id,
            status="QUEUED",
            service="voice2soap",
            message="Voice to SOAP conversion job started",
            child_jobs=child_jobs
        )

    def _start_soap_generation(self, parent_job_id: str) -> None:
        """SOAP生成ジョブを開始"""
        generate_soap_job = Job(
            job_type=JobType.GENERATE_SOAP,
            job_status=JobStatus.PENDING,
            parent_job_id=parent_job_id,
            payload=json.dumps({
                "parent_job_id": parent_job_id
            }),
            created_at=TimeUtil.now_str(),
            updated_at=TimeUtil.now_str()
        )
        generate_soap_job.save()

        # SQSにメッセージを送信
        queue_name = self.aws_config["SQS_JOB_QUEUE"]
        message_body = json.dumps({
            "job_id": generate_soap_job.job_id,
            "job_type": JobType.GENERATE_SOAP.value,
            "parent_job_id": parent_job_id
        })
        
        self.sqs_client.send_message(queue_name, message_body)
        logger.info("Started SOAP generation job: %s", generate_soap_job.job_id)

    def _extract_upload_id_from_job(self, job: Job) -> str:
        """ジョブのpayloadからupload_idを抽出"""
        try:
            payload = json.loads(job.payload) if job.payload else {}
            return payload.get("upload_id", "unknown")
        except json.JSONDecodeError:
            return "unknown"

    def _get_transcription_text_from_job(self, job: Job) -> str:
        """Transcribeジョブから文字起こしテキストを取得"""
        try:
            bucket = self.aws_config['S3_BUCKET']
            transcribe_result_key = f"{TRANSCRIPTION_DESTINATION_KEY_PREFIX}{job.job_id}/{TRANSCRIBE_DESTINATION_FILENAME}"
            
            transcribe_result = self.s3_client.get_json_object(bucket, transcribe_result_key)
            results = transcribe_result.get('results', {})
            transcripts = results.get('transcripts', [])
            
            if transcripts:
                return transcripts[0].get('transcript', '')
            return ""
        except Exception as e:
            logger.warning("Failed to get transcription text for job %s: %s", job.job_id, e)
            return ""