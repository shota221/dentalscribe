import time
from typing import Dict, Any, Optional
from chalicelib.clients.aws.base import BaseAWSClient
from botocore.exceptions import ClientError
from chalicelib.exceptions import TranscribeError

class TranscribeClient(BaseAWSClient):
    def __init__(self, region: Optional[str] = None):
        super().__init__('transcribe', region)

    def start_transcription_job(
        self,
        job_name: str,
        media_uri: str,
        output_bucket: str = None,
        output_key: str = None,
        settings: Dict = None
    ) -> Dict:
        """
        音声ファイルの文字起こしジョブを開始します。

        Args:
            job_name: トランスクリプションジョブの一意の名前
            media_uri: 入力音声ファイルのS3 URI
            language_code: 音声の言語コード（デフォルト: 日本語）
            output_bucket: 出力先のS3バケット名（オプション）
            output_key: 出力先のS3キー（オプション）
            settings: その他のトランスクリプション設定

        Returns:
            Dict: 作成されたトランスクリプションジョブの情報
        """
        try:
            language_code = self.aws_config["TRANSCRIBE_LANGUAGE_CODE"]
            max_speaker_labels = self.aws_config["TRANSCRIBE_MAX_SPEAKER_LABELS"]

            params = {
                'TranscriptionJobName': job_name,
                'Media': {'MediaFileUri': media_uri},
                'LanguageCode': language_code,
                'Settings': {
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': max_speaker_labels
                }
            }

            if output_bucket and output_key:
                params['OutputBucketName'] = output_bucket
                params['OutputKey'] = output_key

            if settings:
                params.update(settings)

            response = self.client.start_transcription_job(**params)
            return response['TranscriptionJob']['TranscriptionJobName']

        except ClientError as e:
            raise TranscribeError(message=e.response['Error']['Message'])

    def get_transcription_job(self, job_name: str) -> Dict:
        """
        トランスクリプションジョブの状態を取得します。

        Args:
            job_name: トランスクリプションジョブ名

        Returns:
            Dict: ジョブの情報
        """
        try:
            response = self.client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            return response['TranscriptionJob']
        except ClientError as e:
            raise TranscribeError(message=e.response['Error']['Message'])

    def wait_for_completion(
        self,
        job_name: str,
        polling_interval: int = 30,
        timeout: int = 3600
    ) -> Dict:
        """
        トランスクリプションジョブが完了するまで待機します。

        Args:
            job_name: トランスクリプションジョブ名
            polling_interval: ステータスチェックの間隔（秒）
            timeout: タイムアウトまでの最大待機時間（秒）

        Returns:
            Dict: 完了したジョブの情報

        Raises:
            TimeoutError: 指定された時間内にジョブが完了しなかった場合
        """
        start_time = time.time()
        while True:
            job = self.get_transcription_job(job_name)
            status = job['TranscriptionJobStatus']

            if status == 'COMPLETED':
                return job
            elif status == 'FAILED':
                raise Exception(
                    f"Transcription job failed: {job.get('FailureReason', 'Unknown error')}"
                )

            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Transcription job did not complete within {timeout} seconds"
                )

            time.sleep(polling_interval)

    def delete_transcription_job(self, job_name: str) -> None:
        """
        トランスクリプションジョブを削除します。

        Args:
            job_name: 削除するトランスクリプションジョブ名
        """
        try:
            self.client.delete_transcription_job(
                TranscriptionJobName=job_name
            )
        except ClientError as e:
            raise TranscribeError(message=e.response['Error']['Message'])

    def list_transcription_jobs(
        self,
        status: str = None,
        job_name_contains: str = None,
        next_token: str = None,
        max_results: int = 100
    ) -> Dict:
        """
        トランスクリプションジョブの一覧を取得します。

        Args:
            status: ジョブステータスでフィルタリング（オプション）
            job_name_contains: ジョブ名に含まれる文字列でフィルタリング（オプション）
            next_token: ページネーショントークン（オプション）
            max_results: 1回のリクエストで取得する最大結果数

        Returns:
            Dict: トランスクリプションジョブのリスト
        """
        try:
            params = {'MaxResults': max_results}
            
            if status:
                params['Status'] = status
            if job_name_contains:
                params['JobNameContains'] = job_name_contains
            if next_token:
                params['NextToken'] = next_token

            response = self.client.list_transcription_jobs(**params)
            return response
        except ClientError as e:
            raise TranscribeError(message=e.response['Error']['Message'])