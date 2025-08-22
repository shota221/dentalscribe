import json
import uuid
import logging
import os
from chalicelib.clients.aws.s3 import S3Client
from typing import List, Dict, Any, Generator, Optional, Tuple, Iterator
from chalicelib.utils.decorators import result_handler
from chalicelib.utils.time_util import TimeUtil
from chalicelib.constants import TRANSCRIPTION_SOURCE_KEY_PREFIX, TRANSCRIPTION_DESTINATION_KEY_PREFIX, TRANSCRIBE_DESTINATION_FILENAME, STORAGE_KEY_PREFIX
from chalicelib.config import Config
from chalicelib.exceptions import ValidationError
from chalicelib.responses import GetVoiceUploadUrlResponse

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
        
        # ファイル拡張子の検証
        file_extension = os.path.splitext(filename)[1].lower()
        if not file_extension or file_extension not in valid_extensions:
            raise ValidationError(f"Invalid file extension: {file_extension}. Supported extensions are: {', '.join(valid_extensions)}")


        # ユニークなupload_idを生成
        upload_id = f"upload-{uuid.uuid4()}"
        
        # S3キーを生成: transcription/source/{upload_id}.{ext}
        s3_key = f"{TRANSCRIPTION_SOURCE_KEY_PREFIX}{upload_id}{file_extension}"
        
        # Content-Typeを決定
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        # S3クライアントを初期化
        s3_client = S3Client()
        
        # バケット名を設定から取得
        bucket_name = self.aws_config['S3_BUCKET']
        
        # presigned URLを生成（1時間の有効期限）
        expiration = 3600
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