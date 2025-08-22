from typing import Optional, Any, Dict
from chalicelib.exceptions.base import BaseError


class ValidationError(BaseError):
    """バリデーション失敗時の例外"""
    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VAL001",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, 400, details)

    def add_field_error(self, field: str, message: str) -> None:
        """フィールドごとのエラーを追加"""
        if 'field_errors' not in self.details:
            self.details['field_errors'] = {}
        self.details['field_errors'][field] = message
