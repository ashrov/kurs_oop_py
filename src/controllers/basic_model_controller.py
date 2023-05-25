from abc import ABC, abstractmethod

from src.db import TableViewable


class BasicModelController(ABC):
    """
    Родительский класс для контроллеров моделей.
    """

    @staticmethod
    @abstractmethod
    def show_edit_window(master, config, db_obj: TableViewable | None = None):
        """
        Метод для открытия окна изменения модели
        """
        ...
