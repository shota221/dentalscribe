from chalicelib.requests.base import BaseSchema


class CreateVoice2SoapJobSchema(BaseSchema):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "anyOf": [
            {"required": ["upload_ids"]},
            {"required": ["upload_id"]},  # 後方互換性のため一旦残す
            {"required": ["source_s3_key"]}
        ],
        "properties": {
            "upload_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "description": "Array of Upload IDs from storage service"
            },
            "upload_id": {
                "type": "string",
                "description": "Single Upload ID from storage service (deprecated, use upload_ids)"
            },
            "source_s3_key": {
                "type": "string",
                "description": "Direct S3 key to the voice file"
            }
        }
    }
