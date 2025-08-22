import logging
import json
from typing import Dict, Any

class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # ISO形式の時間フォーマット
        self.datefmt = '%Y-%m-%dT%H:%M:%S%z'
        
        # 基本情報の取得
        log_data: Dict[str, Any] = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'message': record.getMessage(),
        }
        
        # エラー情報の追加（もしあれば）
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # extra情報の追加
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'thread', 'threadName']:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)
    
def setup_logging():
    # ルートロガーの取得
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラーを削除
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    # 新しいハンドラーの作成
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)