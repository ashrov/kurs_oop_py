import re

from customtkinter import CTkFrame, CTkButton
from sqlalchemy.exc import IntegrityError, DatabaseError, DataError

from ..table import Table
from .basic_edit_window import BaseEditWindow, EditResult
from src.db import get_database, Reader, Session, add_it_to_history, EventType
from src.exc import ModelEditError
from src.config_models import ConfigModel


class ReaderEditWindow(BaseEditWindow):
    def __init__(self, config: ConfigModel, *args, db_obj: Reader = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Изменение книги")

        if not db_obj:
            db_obj = Reader()
            self.edit_result = EditResult.NEW
        else:
            self.edit_result = EditResult.EDITED

        self._firstname_entry = self._add_field_row("Имя", db_obj.firstname)
        self._lastname_entry = self._add_field_row("Фамилия", db_obj.lastname)
        self._phone_entry = self._add_field_row("Номер телефона", db_obj.phone)

        self._reader = db_obj

        self.add_bottom_buttons()

    @add_it_to_history(EventType.NEW_READER)
    @get_database
    def save(self, db: Session) -> EditResult:
        try:
            self._reader.firstname = self.process_field(self._firstname_entry)
            self._reader.lastname = self.process_field(self._lastname_entry)
            self._reader.phone = self.process_field(self._phone_entry)

            number_pattern = re.compile(r"\+7\w{10}")
            if number_pattern.match(self._reader.phone):
                db.add(self._reader)
                db.commit()
            else:
                raise ModelEditError("Некорректный номер телефона")
        except IntegrityError:
            raise ModelEditError("Ошибка, номер телефона уже был зарегистрирован ранее")
        except DatabaseError as e:
            raise ModelEditError(e.args)

        return self.edit_result
