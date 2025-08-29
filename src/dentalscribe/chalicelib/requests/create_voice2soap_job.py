from chalicelib.requests.base import BaseSchema


class CreateVoice2SoapJobSchema(BaseSchema):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "anyOf": [
            {"required": ["upload_id"]},
            {"required": ["source_s3_key"]}
        ],
        "properties": {
            "upload_id": {
                "type": "string",
                "description": "Upload ID from storage service"
            },
            "source_s3_key": {
                "type": "string",
                "description": "Direct S3 key to the voice file"
            }
        }
    }
