from enum import Enum

class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class JobType(str, Enum):
    VOICE_TO_SOAP = "VOICE_TO_SOAP"
    TRANSCRIBE    = "TRANSCRIBE"
    GENERATE_SOAP = "GENERATE_SOAP"