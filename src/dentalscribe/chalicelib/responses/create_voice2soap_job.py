from dataclasses import dataclass
from typing import List, Optional
from chalicelib.enums.job import JobStatus

@dataclass 
class ChildJobInfo:
    job_id: str
    upload_id: str
    status: str
    service: str

@dataclass
class CreateVoice2SoapJobResponse:
    job_id: str
    status: str
    service: str
    message: str
    child_jobs: List[ChildJobInfo]