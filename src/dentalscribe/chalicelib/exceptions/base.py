from typing import Optional, Any, Dict

class BaseError(Exception):
    """基底となる例外クラス"""
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """例外情報を辞書形式で返す"""
        error_dict = {
            'message': self.message,
            'status_code': self.status_code
        }
        if self.error_code:
            error_dict['error_code'] = self.error_code
        if self.details:
            error_dict['details'] = self.details
        return error_dict
