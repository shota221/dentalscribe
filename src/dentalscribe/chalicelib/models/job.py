import uuid
from typing import Dict, Optional, Any
from dataclasses import dataclass
from chalicelib.enums.job import JobStatus, JobType
from chalicelib.config import Config
from chalicelib.constants import PARENT_JOB_ID_NONE
from chalicelib.models.dynamodb import DynamoDBModel
from chalicelib.utils.time_util import TimeUtil

@dataclass
class Job(DynamoDBModel):
    job_type: JobType | str
    job_status: JobStatus | str
    job_id: Optional[str] = None
    parent_job_id: Optional[str] = None
    total_child_jobs: Optional[int] = None
    completed_child_jobs: Optional[int] = None
    failed_child_jobs: Optional[int] = None
    payload: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    ttl: Optional[int] = None

    @classmethod
    def table_name(cls):
        return Config.get_aws_config()["DYNAMODB_JOB_TABLE"]
    
    @classmethod
    def partition_key_name(cls):
        return "job_id"
    
    def __post_init__(self):
        if not self.job_id:
            self.job_id = str(uuid.uuid4())
        if isinstance(self.job_type, str):
            self.job_type = JobType(self.job_type)
        if isinstance(self.job_status, str):
            self.job_status = JobStatus(self.job_status)
        if not self.parent_job_id:
            self.parent_job_id = PARENT_JOB_ID_NONE # GSIのソートキーに使うため、親ジョブがない場合は"NONE"を設定

    def save(self):
        if not self.ttl:
            self.ttl = int(TimeUtil.timestamp() + Config.get_aws_config()['DYNAMODB_JOB_TTL_SECONDS'])
        return super().save()