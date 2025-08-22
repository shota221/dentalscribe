from dataclasses import dataclass

@dataclass
class SoapData:
    subjective: str
    objective: str
    assessment: str
    plan: str

@dataclass
class GetVoice2SoapJobResponse:
    job_id: str
    status: str
    transcription_text: str
    soap_data: SoapData

