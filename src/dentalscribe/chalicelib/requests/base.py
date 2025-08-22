from typing import Dict, Any, List
from aws_lambda_powertools.utilities.validation import validate, SchemaValidationError
from chalicelib.exceptions import ValidationError

class BaseSchema:
    schema: Dict[str, Any] = {}

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        try:
            validate(event=data, schema=cls.schema)
        except SchemaValidationError as e:
            raise ValidationError(str(e))
