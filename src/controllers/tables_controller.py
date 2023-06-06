from typing import Type, Iterable, Callable

from ..interface import Table, RowAction
from ..db import TableViewable


def refresh_tables(tables: Iterable[Type[TableViewable]] | Type[TableViewable] | None = None):
    def decorator(f: Callable):
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            TablesController.refresh(tables)
            return result

        return wrapper
    return decorator


class TablesController:
    _tables: dict[Type[TableViewable], Table] = dict()

    @classmethod
    def create_table(cls, *args, **kwargs) -> Table:
        new_table = Table(*args, **kwargs)
        cls._tables[new_table.get_db_class()] = new_table

        return new_table

    @classmethod
    def refresh_all(cls):
        for table in cls._tables.values():
            table.refresh()

    @classmethod
    def refresh(cls, tables: Iterable[Type[TableViewable]] | Type[TableViewable] | None = None):
        if tables is None:
            cls.refresh_all()
        elif isinstance(tables, Iterable):
            for table in tables:
                if table in cls._tables:
                    cls._tables[table].refresh()
        elif issubclass(tables, TableViewable) and (tables in cls._tables):
            cls._tables[tables].refresh()
