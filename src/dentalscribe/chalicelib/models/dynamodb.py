from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from chalicelib.utils.time_util import TimeUtil
from chalicelib.models.base import BaseModel
from chalicelib.clients.aws import AWSClients
from chalicelib.config import Config
from chalicelib.exceptions import DynamoDBError

@dataclass
class DynamoDBModel(BaseModel):
    @classmethod
    @abstractmethod
    def table_name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def partition_key_name(cls) -> str:
        pass

    @classmethod
    def sort_key_name(cls) -> Optional[str]:
        return None

    def save(self) -> Dict:
        if hasattr(self, "created_at") and not getattr(self, "created_at"):
            setattr(self, "created_at", TimeUtil.now_str())
        if hasattr(self, "updated_at"):
            setattr(self, "updated_at", TimeUtil.now_str())
        
        try:
            dict_data = asdict(self)
            item = self.as_item(dict_data)
            table_name = self.table_name()
            return AWSClients().get_dynamodb().put_item(table_name, item)
        except Exception as e:
            raise DynamoDBError(f"Failed to save item to DynamoDB: {str(e)}")

    def delete(self) -> Dict:
        try:
            partition_key_value = getattr(self, self.partition_key_name())
            key = {
                self.partition_key_name(): self._convert_to_dynamo_type(partition_key_value)
            }

            if self.sort_key_name():
                sort_key_value = getattr(self, self.sort_key_name())
                key[self.sort_key_name()] = self._convert_to_dynamo_type(sort_key_value)

            table_name = self.table_name()
            return AWSClients().get_dynamodb().delete_item(table_name, key)
        except Exception as e:
            raise DynamoDBError(f"Failed to delete item from DynamoDB: {str(e)}")

    @classmethod
    def find(cls, key: Dict) -> Optional['DynamoDBModel']:
        try:
            table_name = cls.table_name()
            item = AWSClients().get_dynamodb().get_item(table_name, key)
            return cls.from_item(item)
        except Exception as e:
            raise DynamoDBError(f"Failed to find item in DynamoDB: {str(e)}")

    @classmethod
    def filter(cls, index_name: Optional[str], key: Dict) -> List['DynamoDBModel']:
        try:
            table_name = cls.table_name()
            items = AWSClients().get_dynamodb().filter_items(table_name, index_name, key)
            return [cls.from_item(item) for item in items if item]
        except Exception as e:
            raise DynamoDBError(f"Failed to filter items in DynamoDB: {str(e)}")
        

    @classmethod
    def query(cls, index_name: Optional[str], key_condition_expression: str, expression_attribute_values: Dict[str, Any]) -> List['DynamoDBModel']:
        try:
            table_name = cls.table_name()
            items = AWSClients().get_dynamodb().query_items(table_name, index_name, key_condition_expression, expression_attribute_values)
            return [cls.from_item(item) for item in items if item]
        except Exception as e:
            raise DynamoDBError(f"Failed to query items in DynamoDB: {str(e)}")

    @classmethod
    def _convert_to_dynamo_type(cls, value: Any) -> Dict:
        if value is None:
            return {"NULL": True}
        elif isinstance(value, str):
            return {"S": value}
        elif isinstance(value, bool):
            return {"BOOL": value}
        elif isinstance(value, (int, float)):
            return {"N": str(value)}
        elif isinstance(value, datetime):
            return {"S": value.isoformat()}
        elif isinstance(value, Enum):
            return cls._convert_to_dynamo_type(value.value)
        elif isinstance(value, dict):
            return {"M": cls.as_item(value)}
        elif isinstance(value, (list, tuple, set)):
            if not value:
                return {"L": []}
            return {"L": [cls._convert_to_dynamo_type(v) for v in value]}
        else:
            raise ValueError(f"Unsupported type for DynamoDB: {type(value)}")

    @classmethod
    def _convert_from_dynamo_type(cls, value: Dict) -> Any:
        if not isinstance(value, dict):
            return value
        
        for type_key, type_value in value.items():
            if type_key == "NULL" and type_value:
                return None
            elif type_key == "S":
                return type_value
            elif type_key == "N":
                # 整数か小数点数かを判断
                return int(type_value) if float(type_value).is_integer() else float(type_value)
            elif type_key == "BOOL":
                return type_value
            elif type_key == "M":
                return {k: cls._convert_from_dynamo_type(v) for k, v in type_value.items()}
            elif type_key == "L":
                return [cls._convert_from_dynamo_type(v) for v in type_value]
        return value

    @classmethod
    def as_item(cls, dict_data: Dict) -> Dict:
        if not isinstance(dict_data, dict):
            return cls._convert_to_dynamo_type(dict_data)
        
        item = {}
        for key, value in dict_data.items():
            try:
                item[key] = cls._convert_to_dynamo_type(value)
            except ValueError as e:
                raise ValueError(f"Error converting field '{key}': {str(e)}")
        return item

    @classmethod
    def from_item(cls, item: Optional[Dict]) -> Optional['DynamoDBModel']:
        if not item:
            return None
        
        try:
            data = {
                key: cls._convert_from_dynamo_type(value)
                for key, value in item.items()
            }

            return cls(**data)
        except Exception as e:
            raise DynamoDBError(f"Failed to convert DynamoDB item to model: {str(e)}")