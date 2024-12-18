import os
import json
from deployment.logger import get_logger
from functools import wraps
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

logger = get_logger()


def load_json_file(file_path):
    try:
        with open(file_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        raise


def load_text_file(file_path):
    try:
        with open(file_path) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading text file {file_path}: {e}")
        raise


def handle_builder_exceptions(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return {"status": "success", "message": f"{func.__name__} executed successfully"}
        except HttpResponseError as e:
            self.logger.error(f"HTTP response error in {func.__name__}: {e.message}")
            raise  # Re-raise the exception to propagate it up the stack
        except ResourceNotFoundError as e:
            self.logger.error(f"Resource not found error in {func.__name__}: {e.message}")
            raise  # Re-raise the exception to propagate it up the stack
        except Exception as e:
            self.logger.error(f"Error in {func.__name__}: {str(e)}")
            raise  # Re-raise the exception to propagate it up the stack
    return wrapper
