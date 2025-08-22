from typing import Dict, Any
from chalicelib.prompts.voice2soap import Voice2SoapPrompt
from chalicelib.prompts.schemas.voice2soap import Voice2SoapSchema


class PromptFactory:
    @staticmethod
    def create_voice2soap_prompt(voice_record: str) -> str:
        prompt = Voice2SoapPrompt()
        schema = Voice2SoapSchema().schema
        return prompt.format(voice_record=voice_record, schema=schema)
