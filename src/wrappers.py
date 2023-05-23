from typing import Callable
from logging import Logger, getLogger, DEBUG


def log_it(logger: Logger = None, level: int = DEBUG):
    if not logger:
        logger = getLogger(__name__)

    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            logger.log(level, f"Starting {f.__name__} function")
            result = f(*args, **kwargs)
            logger.log(level, f"Function {f.__name__} handled")

            return result
        return wrapper
    return decorator
