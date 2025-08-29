from typing import Dict, Any
import json
from chalicelib.prompts.voice2soap import Voice2SoapPrompt
from chalicelib.prompts.schemas.voice2soap import Voice2SoapSchema


class PromptFactory:
    @staticmethod
    def create_voice2soap_prompt(voice_record: str) -> str:
        prompt = Voice2SoapPrompt()
        schema_instance = Voice2SoapSchema()
        schema_json = json.dumps(schema_instance.schema, ensure_ascii=False, indent=2)
        
        return prompt.format(
            voice_record=voice_record,
            schema=schema_json
        )
