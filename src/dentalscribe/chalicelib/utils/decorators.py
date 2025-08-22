import functools
import time
import json
from typing import Optional, Callable, Type, TypeVar
from logging import getLogger, INFO, DEBUG, ERROR
from http import HTTPStatus
from dataclasses import asdict, is_dataclass
from chalicelib.exceptions.handler import handle_error
from chalicelib.exceptions import ValidationError
from botocore.exceptions import ClientError
from chalicelib.utils.time_util import TimeUtil
from chalice import Response

logger = getLogger(__name__)

def result_handler(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            body = asdict(result) if is_dataclass(result) else result
            return Response(
                status_code=HTTPStatus.OK,
                body=body,
            )
        except Exception as e:
            return handle_error(e)

    return wrapper

def stream_handler(func):
    def wrapper(*args, **kwargs):
        try:
            for result in func(*args, **kwargs):            
                yield json.dumps(asdict(result), ensure_ascii=False) if is_dataclass(result) else result
        except Exception as e:
            error = handle_error(e)
            if isinstance(e, ValidationError):
                yield json.dumps(error.body, ensure_ascii=False)
                return
            else:
                yield ""

    return wrapper

def handle_aws_exceptions(exception_class_thrown: Type[Exception]):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                error_message = e.response['Error']['Message']
                raise exception_class_thrown(message=error_message) from e
        return wrapper
    return decorator