from typing import Optional
import boto3
from botocore.config import Config
from chalicelib.config import Config as AppConfig

class BaseAWSClient:
    def __init__(self, service_name: str, region: Optional[str] = None, max_retries: Optional[int] = None, retry_mode: Optional[str] = None):
        self.config = self._build_config(region, max_retries, retry_mode)
        self.aws_config = AppConfig.get_aws_config()
        self.client = boto3.client(
            service_name,
            config=self.config
        )

    def _build_config(self, region: Optional[str] = None, max_retries: Optional[int] = None, retry_mode: Optional[str] = None):
        return Config(
            region_name=region or AppConfig.get_aws_config()['DEFAULT_REGION'],
            retries={
                'max_attempts': max_retries or AppConfig.get_aws_config()['MAX_RETRIES'],
                'mode': retry_mode or AppConfig.get_aws_config()['RETRY_MODE']
            }
        )

    def get_region(self):
        return self.config.region_name
