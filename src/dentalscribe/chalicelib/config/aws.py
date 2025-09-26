from typing import Dict
from chalicelib.config.base import BaseConfig


class AWSConfig(BaseConfig):
    """AWS関連設定を管理するクラス"""

    @classmethod
    def get_aws_config(cls) -> Dict[str, str]:
        """AWS全般設定を取得"""
        return {
            "DEFAULT_REGION": cls._get_env_var("AWS_DEFAULT_REGION", "ap-northeast-1"),
            "MAX_RETRIES": cls._get_env_var("AWS_MAX_RETRIES", 3),
            "RETRY_MODE": cls._get_env_var("AWS_RETRY_MODE", "standard"),
        }

    @classmethod
    def get_bedrock_config(cls) -> Dict[str, str]:
        """Bedrock設定を取得"""
        return {
            "BEDROCK_REGION": cls._get_env_var("BEDROCK_REGION", required=True),
            "BEDROCK_MODEL_ID": cls._get_env_var("BEDROCK_MODEL_ID", required=True),
       }

    @classmethod
    def get_s3_config(cls) -> Dict[str, str]:
        """S3設定を取得"""
        return {
            "S3_BUCKET": cls._get_env_var("S3_BUCKET", required=True),
            "UPLOAD_URL_EXPIRES_IN": cls._get_env_int("UPLOAD_URL_EXPIRES_IN", 3600),
            "DOWNLOAD_URL_EXPIRES_IN": cls._get_env_int("DOWNLOAD_URL_EXPIRES_IN", 300),
        }

    @classmethod
    def get_dynamodb_config(cls) -> Dict[str, str]:
        """DynamoDB設定を取得"""
        return {
            "DYNAMODB_JOB_TABLE": cls._get_env_var("DYNAMODB_JOB_TABLE", required=True),
            "DYNAMODB_TTL_ATTRIBUTE": cls._get_env_var("DYNAMODB_TTL_ATTRIBUTE", "ttl"),
            "DYNAMODB_JOB_TTL_SECONDS": cls._get_env_int(
                "DYNAMODB_JOB_TTL_SECONDS", 60 * 60 * 24 * 7
            ),
        }

    @classmethod
    def get_sqs_config(cls) -> Dict[str, str]:
        """SQS設定を取得"""
        return {
            "SQS_JOB_QUEUE": cls._get_env_var("SQS_JOB_QUEUE", required=True),
            "SQS_JOB_FAILED_QUEUE": cls._get_env_var("SQS_JOB_FAILED_QUEUE", required=True),
        }

    @classmethod
    def get_transcribe_config(cls) -> Dict[str, str]:
        """Transcribe設定を取得"""
        return {
            "TRANSCRIBE_LANGUAGE_CODE": cls._get_env_var("TRANSCRIBE_LANGUAGE_CODE", "ja-JP"),
            "TRANSCRIBE_MAX_SPEAKER_LABELS": cls._get_env_var("TRANSCRIBE_MAX_SPEAKER_LABELS", 16),
        }

    @classmethod
    def get_lambda_config(cls) -> Dict[str, str]:
        """Lambda設定を取得"""
        return {
            "AUTHORIZER_LAMBDA_ARN": cls._get_env_var("AUTHORIZER_LAMBDA_ARN", required=True),
        }
