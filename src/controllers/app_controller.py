from typing import Any, Callable, Iterable, Type
from functools import wraps

from ..db import TableViewable


class AppController:
    _app: Any

    @classmethod
    def set_app(cls, app: Any):
        cls._app = app

    @classmethod
    def refresh(cls, tables: Iterable[Type[TableViewable]] | Type[TableViewable] | None = None):
        cls._app.refresh(tables)


def refresh_tables(tables: Iterable[Type[TableViewable]] | Type[TableViewable] | None = None):
    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            AppController.refresh(tables)
            return result

        return wrapper
    return decorator
