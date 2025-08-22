from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from abc import ABC, abstractmethod

@dataclass
class BaseModel(ABC):
    def to_dict(self) -> Dict[str, Any]:
        """モデルを辞書に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """辞書からモデルを生成"""
        return cls(**data)