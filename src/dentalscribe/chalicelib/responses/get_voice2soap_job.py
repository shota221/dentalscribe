from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SoapData:
    subjective: str
    objective: str
    assessment: str
    plan: str

@dataclass
class ChildJobDetail:
    job_id: str
    upload_id: str
    status: str
    transcription_text: str

@dataclass
class GetVoice2SoapJobResponse:
    job_id: str
    status: str
    transcription_text: str
    soap_data: Optional[SoapData]
    child_jobs: List[ChildJobDetail]

