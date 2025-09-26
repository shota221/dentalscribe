import json
import uuid
import logging
import os
from chalicelib.clients.aws.s3 import S3Client
from typing import List, Dict, Any, Generator, Optional, Tuple, Iterator
from chalicelib.utils.decorators import result_handler
from chalicelib.utils.time_util import TimeUtil
from chalicelib.constants import (
    TRANSCRIPTION_SOURCE_KEY_PREFIX,
    TRANSCRIPTION_DESTINATION_KEY_PREFIX,
    TRANSCRIBE_DESTINATION_FILENAME,
    STORAGE_KEY_PREFIX,
    UPLOAD_ID_REGEX,
)
from chalicelib.config import Config
from chalicelib.exceptions import ValidationError
from chalicelib.responses import GetVoiceUploadUrlResponse, GetVoiceDownloadUrlResponse
from botocore.exceptions import ClientError
import re

logger = logging.getLogger(__name__)

class StorageService:

    def __init__(self):
        self.s3_client = S3Client()
        self.aws_config = Config.get_aws_config()

        
    @result_handler
    def get_voice_upload_url(self, query_params: Dict[str, Any]) -> GetVoiceUploadUrlResponse:

        if not query_params or 'filename' not in query_params:
            raise ValidationError("Missing required query parameter: filename")

        filename = query_params['filename']

        valid_extensions = {
            '.mp3', '.mp4', '.m4a', '.wav', '.flac', 
            '.amr', '.ogg', '.webm'
        }

        content_type_map = {
            '.mp3': 'audio/mpeg',
            '.mp4': 'audio/mp4',
            '.m4a': 'audio/mp4',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.amr': 'audio/amr',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm'
        }
        
        file_extension = os.path.splitext(filename)[1].lower()
        if not file_extension or file_extension not in valid_extensions:
            raise ValidationError(f"Invalid file extension: {file_extension}. Supported extensions are: {', '.join(valid_extensions)}")


        upload_id = f"upload-{uuid.uuid4()}"
        
        s3_key = f"{TRANSCRIPTION_SOURCE_KEY_PREFIX}{upload_id}{file_extension}"
        
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        s3_client = S3Client()
        
        bucket_name = self.aws_config['S3_BUCKET']
        expiration = int(self.aws_config.get('UPLOAD_URL_EXPIRES_IN', 3600))
        presigned_url = s3_client.generate_upload_url(
            bucket=bucket_name,
            key=s3_key,
            expiration=expiration,
            content_type=content_type
        )
        
        return GetVoiceUploadUrlResponse(
            upload_id=upload_id,
            presigned_url=presigned_url,
            expires_in=expiration,
            s3_key=s3_key,
            content_type=content_type,
            original_filename=filename
        )

    @result_handler
    def get_voice_download_url(self, query_params: Dict[str, Any]) -> GetVoiceDownloadUrlResponse:
        """既存upload_idの音声ファイルをダウンロードするための一時URLを返す"""

        if not query_params or 'upload_id' not in query_params:
            raise ValidationError("Missing required query parameter: upload_id")

        upload_id = query_params['upload_id']

        if not re.match(UPLOAD_ID_REGEX, upload_id):
            raise ValidationError("Invalid upload_id format")

        # 現在の仕様ではDynamoDB等にuploadレコードを保持していないため、
        # プレフィックス検索でS3上の実体を確認する（PoC想定）。
        bucket_name = self.aws_config['S3_BUCKET']
        prefix = f"{TRANSCRIPTION_SOURCE_KEY_PREFIX}{upload_id}"
        objects = self.s3_client.list_objects(bucket_name, prefix)

        if not objects:
            raise ValidationError("Upload not found")

        # 最初の一致オブジェクトを採用
        obj = objects[0]
        key = obj['Key']
        size = obj.get('Size')

        # ContentType取得（ヘッダのみ）
        content_type = 'application/octet-stream'
        try:
            head = self.s3_client.client.head_object(Bucket=bucket_name, Key=key)
            content_type = head.get('ContentType', content_type)
            size = head.get('ContentLength', size)
        except ClientError as e:
            logger.warning("Failed to head_object for %s: %s", key, e)

        expiration = int(self.aws_config.get('DOWNLOAD_URL_EXPIRES_IN', 300))
        presigned_url = self.s3_client.generate_download_url(
            bucket=bucket_name,
            key=key,
            expiration=expiration,
        )

        return GetVoiceDownloadUrlResponse(
            upload_id=upload_id,
            presigned_url=presigned_url,
            content_type=content_type,
            size=size,
            expires_in=expiration,
            created_at=None  # 将来メタデータ管理を導入した際に設定
        )