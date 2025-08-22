from typing import Dict
from chalicelib.config.base import BaseConfig


class AppConfig(BaseConfig):
    """アプリケーション設定を管理するクラス"""

    @classmethod
    def get_general_config(cls) -> Dict[str, str]:
        """一般設定を取得"""
        return {
            "APP_ENV": cls._get_env_var("APP_ENV", "local"),
            "LOG_LEVEL": cls._get_env_var("LOG_LEVEL", "INFO"),
        }

    @classmethod
    def get_auth_config(cls) -> Dict[str, str]:
        """認証設定を取得"""
        return {
            "JWT_SECRET_KEY": cls._get_env_var("JWT_SECRET_KEY", required=True),
            "JWT_ALGORITHM": cls._get_env_var("JWT_ALGORITHM", "HS256"),
            "JWT_EXPIRATION": cls._get_env_var("JWT_EXPIRATION", 3600),
        }
