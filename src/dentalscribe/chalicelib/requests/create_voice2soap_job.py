from chalicelib.requests.base import BaseSchema


class CreateVoice2SoapJobSchema(BaseSchema):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "required": ["source_s3_key"],
        "properties": {
            "source_s3_key": {
                "type": "string"
            }
        }
    }
