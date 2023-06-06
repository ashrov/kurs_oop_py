from customtkinter import CTkFrame, CTkButton
from sqlalchemy.exc import IntegrityError, DatabaseError, DataError

from .basic_edit_window import BaseEditWindow
from src.db import wrap_with_database, Book, Session
from src.exc import ModelEditError
from src.config_models import ConfigModel
from src.validators import Validator


class BookEditWindow(BaseEditWindow):
    def __init__(self, config: ConfigModel, *args, db_obj: Book = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Изменение книги")

        if not db_obj:
            db_obj = Book()

        self._code_entry = self._add_field_row("Код", db_obj.code)
        self._name_entry = self._add_field_row("Название", db_obj.name)
        self._author_entry = self._add_field_row("Автор", db_obj.author)
        self._count_entry = self._add_field_row("Количество", db_obj.count)

        self._book = db_obj

        self.add_bottom_buttons()
        self.grab_set()

    @wrap_with_database
    def save(self, db: Session):
        try:
            self._book.code = self.process_field(self._code_entry)
            self._book.name = self.process_field(self._name_entry)
            self._book.author = self.process_field(self._author_entry)
            count = self.process_field(self._count_entry)

            Validator.validate_book_count(count, self._book.get_taken_count())
            self._book.count = count

            db.add(self._book)
            db.commit()
        except IntegrityError:
            raise ModelEditError("Ошибка, код книги дублируется")
        except DataError as e:
            raise ModelEditError(e.args[0])
        except DatabaseError as e:
            raise ModelEditError(e.args[0])
