from chalicelib.config.app import AppConfig
from chalicelib.config.aws import AWSConfig


class Config:
    # アプリケーション設定
    @classmethod
    def get_app_config(cls):
        config = {}
        config.update(AppConfig.get_general_config())
        config.update(AppConfig.get_auth_config())
        return config

    @classmethod
    def get_aws_config(cls):
        config = {}
        config.update(AWSConfig.get_aws_config())
        config.update(AWSConfig.get_bedrock_config())
        config.update(AWSConfig.get_s3_config())
        config.update(AWSConfig.get_dynamodb_config())
        config.update(AWSConfig.get_sqs_config())
        config.update(AWSConfig.get_transcribe_config())
        config.update(AWSConfig.get_lambda_config())
        return config

__all__ = [
    'AppConfig',     # アプリケーション設定
    'AWSConfig',     # AWS設定
]
