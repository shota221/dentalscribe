from typing import Dict, Any, Optional, List, Tuple
import json
import boto3
from chalicelib.clients.aws.base import BaseAWSClient
from chalicelib.config import Config as AppConfig
from chalicelib.exceptions import BedrockError


class BedrockClient(BaseAWSClient):
    def __init__(
        self,
        region: Optional[str] = None,
        embedding_region: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_mode: Optional[str] = None,
        text_model_id: Optional[str] = None,
    ):
        super().__init__(
            service_name="bedrock-runtime",
            region=region,
            max_retries=max_retries,
            retry_mode=retry_mode or "adaptive",
        )
        self.embedding_config = self._build_config(region=embedding_region)
        self.embedding_client = boto3.client(
            "bedrock-runtime", config=self.embedding_config
        )
        self.text_model_id = text_model_id or AppConfig.get_aws_config()["BEDROCK_MODEL_ID"]

    def get_embedding_region(self):
        return self.embedding_config.region_name
    
    def get_text_region(self):
        return self.config.region_name
    
    def get_embedding_model_id(self):
        return self.embedding_model_id
    
    def get_text_model_id(self):
        return self.text_model_id

    def generate_text(
        self,
        context: List[str],
        stop_sequences=None,
        max_tokens=8192,
        temperature=1,
        top_p=0.999,
    ) -> Tuple[str, int, int]:
        try:
            response = self.client.invoke_model(
                modelId=self.text_model_id,
                accept="application/json",
                contentType="application/json",
                body=self.__generate_invoke_model_body(
                    self.text_model_id,
                    context,
                    stop_sequences,
                    max_tokens,
                    temperature,
                    top_p,
                ),
            )

            print(response)

            response_body = json.loads(response["body"].read().decode("utf-8"))

            text =  response_body["content"][0]["text"]
            input_tokens = response_body["usage"]["input_tokens"]
            output_tokens = response_body["usage"]["output_tokens"]

            return text, input_tokens, output_tokens

        except Exception as e:
            raise BedrockError(message="Failed to generate text", details={"error": str(e)})

    def generate_embedding(self, text: str, dimensions=1024) -> Tuple[List[float], int]:
        body = json.dumps({"inputText": text, "dimensions": dimensions}).encode("utf-8")

        response = self.embedding_client.invoke_model(
            modelId=self.embedding_model_id,
            accept="*/*",
            contentType="application/json",
            body=body,
        )

        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embedding")
        input_tokens = response_body.get("inputTextTokenCount")

        return embedding, input_tokens

    def stream_message(
        self,
        context: List[str],
        stop_sequences=None,
        max_tokens=8192,
        temperature=1,
        top_p=0.999,
    ):
        bedrock_response = self.client.invoke_model_with_response_stream(
            modelId=self.text_model_id,
            body=self.__generate_invoke_model_body(
                self.text_model_id,
                context,
                stop_sequences,
                max_tokens,
                temperature,
                top_p,
            ),
        )

        return bedrock_response.get("body")

    def __generate_invoke_model_body(
        self,
        model_id: str,
        context: List[str],
        stop_sequences=None,
        max_tokens=1000,
        temperature=1,
        top_p=0.999,
    ):
        if "claude" in model_id:
            return self.__generate_invoke_claude_model_body(
                context, stop_sequences, max_tokens, temperature, top_p
            )

        elif "titan" in model_id:
            return self.__generate_invoke_titan_model_body(
                context, stop_sequences, max_tokens, temperature, top_p
            )

    def __generate_invoke_claude_model_body(
        self,
        context: List[str],
        stop_sequences=None,
        max_tokens=1000,
        temperature=1,
        top_p=0.999,
    ):
        messages = []

        for i, message in enumerate(context):
            messages.append(
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": [{"type": "text", "text": message}],
                }
            )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }

        if stop_sequences:
            body["stop_sequences"] = stop_sequences

        print(body)

        return json.dumps(body)

    def __generate_invoke_titan_model_body(
        self,
        context: list,
        stop_sequences=None,
        max_tokens=1000,
        temperature=1,
        top_p=0.999,
    ):
        input_text = "User: "

        for i, message in enumerate(context):
            if i % 2 == 0:
                input_text += f"{message}\nBot: "
            else:
                input_text += f"{message}\nUser: "

        body = {
            "inputText": input_text,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": top_p,
            },
        }

        if stop_sequences:
            body["textGenerationConfig"]["stopSequences"] = stop_sequences

        return json.dumps(body)
