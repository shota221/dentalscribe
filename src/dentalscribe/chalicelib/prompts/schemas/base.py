from typing import Dict, Any, List
from aws_lambda_powertools.utilities.validation import validate, SchemaValidationError

class BaseSchema:
    schema: Dict[str, Any] = {}
