from chalicelib.prompts.schemas.base import BaseSchema

class Voice2SoapSchema(BaseSchema):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "subjective": {
                "type": "string",
                "description": "主観的情報を記入してください。"
            },
            "objective": {
                "type": "string",
                "description": "客観的情報を記入してください。"
            },
            "assessment": {
                "type": "string",
                "description": "評価を記入してください。"
            },
            "plan": {
                "type": "string",
                "description": "計画を記入してください。"
            }
        },
    }
