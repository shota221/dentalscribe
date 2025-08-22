from typing import Dict, Any, Optional
from chalicelib.clients.aws.base import BaseAWSClient
from chalicelib.exceptions import SQSError

class SQSClient(BaseAWSClient):
    def __init__(self, region: Optional[str] = None):
        super().__init__('sqs', region)

    def send_message(self, queue_name, message_body):
        response = self.client.send_message(
            QueueUrl=self.__queue_url(queue_name),
            MessageBody=message_body            
        )
        return response        

    def __queue_url(self, queue_name):
        queue_url = self.client.get_queue_url(QueueName=queue_name)["QueueUrl"]
        return queue_url