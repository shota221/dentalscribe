from dataclasses import dataclass
from chalicelib.enums.job import JobStatus

@dataclass
class CreateVoice2SoapJobResponse:
    job_id: str