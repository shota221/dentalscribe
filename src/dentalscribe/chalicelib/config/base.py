from typing import Dict, Any
import os


class BaseConfig:
    """設定の基底クラス"""
    
    @classmethod
    def _get_env_var(cls, key: str, default: Any = None, required: bool = False) -> Any:
        """環境変数を取得するヘルパーメソッド"""
        value = os.environ.get(key, default)
        if required and value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    @classmethod
    def _get_env_int(cls, key: str, default: int = None, required: bool = False) -> int:
        """環境変数を整数として取得するヘルパーメソッド"""
        value = cls._get_env_var(key, default, required)
        if value is not None:
            return int(value)
        return value
