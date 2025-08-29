from typing import Dict, Any, Optional
import json
import boto3
from botocore.exceptions import ClientError
from chalicelib.clients.aws.base import BaseAWSClient

class S3Client(BaseAWSClient):
    def __init__(self, region: Optional[str] = None):
        super().__init__('s3', region)
        self.resource = boto3.resource('s3')

    def exists(self, bucket, key):
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise e
        
    def exists_dir(self, bucket, dir):
        if dir and not dir.endswith("/"):
            raise ValueError("dir must end with /")
        response = self.list_objects(bucket, dir)
        return len(response) > 0

    def list_objects(self, bucket, prefix=''):
        paginator = self.client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
        )
        objects = []
        for page in page_iterator:
            if 'Contents' in page:
                objects.extend(page['Contents'])

        return objects

    def get_object(self, bucket, key):
        obj = self.client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()
    
    def get_object_content(self, bucket, key):
        """
        指定されたバケットとキーのオブジェクトの内容を文字列として返す
        
        Parameters:
        bucket (str): S3バケット名
        key (str): オブジェクトのキー
        
        Returns:
        str: オブジェクトの内容（UTF-8デコード済み）
        """
        obj = self.client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read().decode('utf-8')
    
    def get_object_size(self, bucket, key):
        """
        指定されたバケットとキーのオブジェクトのサイズをバイト単位で返す
        
        Parameters:
        bucket (str): S3バケット名
        key (str): オブジェクトのキー
        
        Returns:
        int: オブジェクトのサイズ（バイト）
        
        Raises:
        ClientError: オブジェクトが存在しない場合や他のエラーが発生した場合
        """
        try:
            # head_objectを使用してメタデータのみを取得（本文全体をダウンロードせずに済む）
            response = self.client.head_object(Bucket=bucket, Key=key)
            return response['ContentLength']
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise ValueError(f"Object with key '{key}' does not exist in bucket '{bucket}'")
            raise e
    
    def get_text_object(self, bucket, key):
        obj = self.client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read().decode("utf-8")

    def get_json_object(self, bucket, key):
        obj = self.client.get_object(Bucket=bucket, Key=key)
        json_str = obj["Body"].read().decode("utf-8")
        return json.loads(json_str)
    
    def put_object(self, bucket, key, body, content_type):
        response = self.client.put_object(
            Bucket=bucket, Key=key, Body=body, ContentType=content_type
        )
        return response
    
    def copy_object(self, bucket, key, destination_bucket, destination_key):
        response = self.client.copy_object(
            Bucket=destination_bucket,
            Key=destination_key,
            CopySource={"Bucket": bucket, "Key": key},
        )
        return response

    def delete_object(self, bucket, key):
        response = self.client.delete_object(Bucket=bucket, Key=key)
        return response
    
    def delete_objects(self, bucket, prefix):
        bucket = self.resource.Bucket(bucket)
        response = bucket.objects.filter(Prefix=prefix).delete()
        return response
    
    def download_file(self, bucket, key, file_path):
        self.client.download_file(bucket, key, file_path)


    def list_folders(self, bucket, prefix=''):
        folders = set()
        paginator = self.client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
            Delimiter='/'
        )
        for page in page_iterator:
            if 'CommonPrefixes' in page:
                for common_prefix in page['CommonPrefixes']:
                    folder_name = common_prefix['Prefix'][len(prefix):-1]
                    if folder_name:
                        folders.add(folder_name)
        return sorted(list(folders))

    def generate_upload_url(self, bucket, key, expiration=3600, content_type=None, metadata=None):
        params = {"Bucket": bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type
        if metadata:
            params["Metadata"] = metadata
            
        presigned_url = self.client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expiration,
        )
        return presigned_url