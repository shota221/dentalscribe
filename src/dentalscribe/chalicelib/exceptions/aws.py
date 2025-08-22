from chalicelib.exceptions.base import BaseError
from typing import Optional, Dict, Any


class S3Error(BaseError):
    """S3関連のエラー"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="S3_ERROR", status_code=500, details=details)


class TranscribeError(BaseError):
    """Transcribe関連のエラー"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="TRANSCRIBE_ERROR", status_code=500, details=details)


class BedrockError(BaseError):
    """Bedrock関連のエラー"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="BEDROCK_ERROR", status_code=500, details=details)


class DynamoDBError(BaseError):
    """DynamoDB関連のエラー"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="DYNAMODB_ERROR", status_code=500, details=details)


class SQSError(BaseError):
    """SQS関連のエラー"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="SQS_ERROR", status_code=500, details=details)
