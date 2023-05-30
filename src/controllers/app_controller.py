from typing import Any, Callable, Iterable, Type

from .tables_controller import TablesController
from ..db import TableViewable


def refresh_tables(tables: Iterable[Type[TableViewable]] | Type[TableViewable] | None = None):
    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            TablesController.refresh(tables)
            return result

        return wrapper
    return decorator
