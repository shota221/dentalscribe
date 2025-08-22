import logging
from typing import Dict, Any
from chalicelib.exceptions.base import BaseError
from chalice import Response


logger = logging.getLogger(__name__)


def handle_error(error: Exception) -> Response:
    """例外をAPIレスポンスに変換するハンドラー"""
    if isinstance(error, BaseError):
        # カスタム例外の処理
        error_dict = error.to_dict()

        # LogRecordの予約語と衝突しないように、プレフィックスを付ける
        log_extra = {
            "error_type": error.__class__.__name__,
        }
        # error_dictのキーにプレフィックスを付けて追加
        for key, value in error_dict.items():
            log_extra[f"error_{key}"] = value

        logger.error(error.message, extra=log_extra)

        return Response(body=error_dict, status_code=error.status_code)
    else:
        # 予期せぬ例外の処理

        logger.error(
            "An unexpected error occurred",
            exc_info=True,
            extra={"error_type": error.__class__.__name__, "error_message": str(error)},
        )

        return Response(
            body={"message": "An unexpected error occurred", "status_code": 500},
            status_code=500,
        )
