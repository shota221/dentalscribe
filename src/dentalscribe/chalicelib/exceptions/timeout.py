from typing import Optional, Any, Dict
from chalicelib.exceptions.base import BaseError

class RequestTimeoutError(BaseError):
    """タイムアウト例外クラス"""
    def __init__(
        self,
        message: str = "Request Timeout",
        error_code: Optional[str] = None,
        status_code: int = 408,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code or "TIMEOUT001",
            status_code=status_code,
            details=details or {}
        )