from typing import Any, Dict
from chalicelib.exceptions import ValidationError

def validate_request_data(data: Dict[str, Any], required_fields: list) -> None:
    """リクエストデータのバリデーション"""
    missing_fields = [
        field for field in required_fields 
        if field not in data or data[field] is None
    ]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}") 