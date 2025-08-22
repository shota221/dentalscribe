from chalicelib.clients.aws.s3 import S3Client
from chalicelib.clients.aws.dynamodb import DynamoDBClient
from chalicelib.clients.aws.transcribe import TranscribeClient
from chalicelib.clients.aws.bedrock import BedrockClient
from chalicelib.clients.aws.sqs import SQSClient


class AWSClients:
    """AWSクライアントのファクトリークラス"""
    
    def __init__(self):
        self._s3_client = None
        self._dynamodb_client = None  
        self._transcribe_client = None
        self._bedrock_client = None
        self._sqs_client = None
    
    def get_s3(self) -> S3Client:
        if self._s3_client is None:
            self._s3_client = S3Client()
        return self._s3_client
    
    def get_dynamodb(self) -> DynamoDBClient:
        if self._dynamodb_client is None:
            self._dynamodb_client = DynamoDBClient()
        return self._dynamodb_client
    
    def get_transcribe(self) -> TranscribeClient:
        if self._transcribe_client is None:
            self._transcribe_client = TranscribeClient()
        return self._transcribe_client
    
    def get_bedrock(self) -> BedrockClient:
        if self._bedrock_client is None:
            self._bedrock_client = BedrockClient()
        return self._bedrock_client
    
    def get_sqs(self) -> SQSClient:
        if self._sqs_client is None:
            self._sqs_client = SQSClient()
        return self._sqs_client
