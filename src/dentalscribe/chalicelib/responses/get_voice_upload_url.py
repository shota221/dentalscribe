from dataclasses import dataclass

@dataclass
class GetVoiceUploadUrlResponse:
    upload_id: str
    presigned_url: str
    expires_in: int
    s3_key: str
    content_type: str
    original_filename: str

