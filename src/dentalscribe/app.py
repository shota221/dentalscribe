from os import environ
import json
import logging
from chalicelib.config import Config
from chalicelib.service_container import ServiceContainer
from chalicelib.utils.logger import setup_logging
from chalicelib.constants import TRANSCRIPTION_DESTINATION_KEY_PREFIX, TRANSCRIBE_DESTINATION_FILENAME
from chalice import Chalice

setup_logging()

logger = logging.getLogger(__name__)

app = Chalice(app_name='dentalscribe')

######################
# api                #
######################

@app.route('/storages/voice-upload-url', methods=['GET'])
def get_voice_upload_url():
    return ServiceContainer.get_storage_service().get_voice_upload_url(app.current_request.query_params)

@app.route('/jobs/voice2soap', methods=['POST'])
def create_voice2soap_job():
    return ServiceContainer.get_job_service().create_voice2soap_job(app.current_request.json_body)

@app.route('/jobs/voice2soap/{job_id}', methods=['GET'])
def get_voice2soap_job(job_id):
    return ServiceContainer.get_job_service().get_voice2soap_job(job_id)

######################
# s3 event handlers  #
######################

@app.on_s3_event(bucket=environ["S3_BUCKET"], events=["s3:ObjectCreated:*"], prefix=TRANSCRIPTION_DESTINATION_KEY_PREFIX, suffix=TRANSCRIBE_DESTINATION_FILENAME)
def on_s3_transcribe_destination_object_created(event):
    logger.info("Object created in S3: %s", event.key)
    # ここで必要な処理を実行

######################
# sqs event handlers #
######################

@app.on_sqs_message(queue=environ["SQS_JOB_QUEUE"])
def on_sqs_message(event):
    logger.info("Received SQS message: %s", event)
    for record in event:
        # record.bodyの最大長は256KB
        ServiceContainer.get_job_service().handle_sqs_message(json.loads(record.body))

@app.on_sqs_message(queue=environ["SQS_JOB_FAILED_QUEUE"])
def on_sqs_failed_message(event):
    logger.info("Received SQS failed message: %s", event)
    for record in event:
        # record.bodyの最大長は256KB
        ServiceContainer.get_job_service().handle_failed_sqs_message(json.loads(record.body))
