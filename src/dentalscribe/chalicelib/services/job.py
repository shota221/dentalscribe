import json
import uuid
import logging
import os
from chalicelib.clients.aws.s3 import S3Client
from typing import List, Dict, Any, Generator, Optional, Tuple, Iterator
from chalicelib.utils.decorators import result_handler
from chalicelib.utils.time_util import TimeUtil
from chalicelib.config import Config
from chalicelib.exceptions import ValidationError
from chalicelib.responses import GetVoice2SoapJobResponse, CreateVoice2SoapJobResponse
from chalicelib.models.job import Job
from chalicelib.enums.job import JobStatus, JobType
from chalicelib.repositories.job import JobRepository

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self):
        self.s3_client = S3Client()
        self.aws_config = Config.get_aws_config()
        self.job_repository = JobRepository()

    @result_handler
    def get_voice2soap_job(self, job_id: str) -> GetVoice2SoapJobResponse:
        pass

    @result_handler
    def create_voice2soap_job(self, json_body: Dict[str, Any]) -> CreateVoice2SoapJobResponse:
        pass


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
            if job.job_type == JobType.VOICE_TO_SOAP:
                self.__handle_voice2soap_job(job)
            elif job.job_type == JobType.TRANSCRIBE:
                self.__handle_transcribe_job(job)
            elif job.job_type == JobType.GENERATE_SOAP:
                self.__handle_generate_soap_job(job)
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

    def __handle_voice2soap_job(self, job: Job) -> None:
        pass

    def __handle_transcribe_job(self, job: Job) -> None:
        pass

    def __handle_generate_soap_job(self, job: Job) -> None:
        pass

    def __handle_failed_job(self, job: Job) -> None:
        pass