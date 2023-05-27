from logging import getLogger
import re

from .basic_model_controller import BasicModelController
from .app_controller import refresh_tables
from ..db import Book, get_database, Session, Reader, BookToReader
from ..interface import CustomInputDialog, ErrorNotification, NotificationWindow, BookEditWindow


logger = getLogger(__name__)


class BooksController(BasicModelController):
    @classmethod
    def give_book_to_reader(cls, master, db_object: Book):
        if db_object.get_available_count() <= 0:
            ErrorNotification("Невозможно выдать книгу, так как она отсутствуют на складе")
            return

        phone_number_dialog = CustomInputDialog(title="Выдача книги",
                                                text="Введите номер телефона читателя")
        phone_number = phone_number_dialog.get_input()

        if phone_number is None:
            logger.info("book giving canceled")
            return

        if not phone_number:
            ErrorNotification(message="Номер телефона не может быть пустым")
            return

        number_pattern = re.compile(r"\+7\w{10}")
        if number_pattern.match(phone_number):
            cls._assign_book_to_reader(db_object, phone_number)
        else:
            ErrorNotification(message="Некорректный номер телефона")
            logger.info(f"incorrect phone number '{phone_number}'")

    @staticmethod
    @refresh_tables((Book, Reader, BookToReader))
    @get_database
    def _assign_book_to_reader(book: Book, phone_number: str, db: Session = None):
        reader = db.query(Reader).where(Reader.phone == phone_number).first()
        if not reader:
            ErrorNotification("Не существует читателя с таким номером телефона.\n\n"
                              "Подсказка: Чтобы выдать книгу на данный номер,\n"
                              "сначала зарегистрируйте читателя с таким номером.")
            return

        confirmation = NotificationWindow(title="Подтвердите действие",
                                          message=f"Выдать книгу читателю с номером телефона '{phone_number}'?",
                                          show_cancel=True,
                                          wait_input=False)
        if confirmation.get_input():
            association = BookToReader(book_id=book.id, reader_id=reader.id)
            reader.books_associations.append(association)
            db.commit()

    @staticmethod
    @refresh_tables((Book, BookToReader))
    def show_edit_window(master, config, db_obj: Book | None = None):
        if not master.top_level_window or not master.top_level_window.winfo_exists():
            master.top_level_window = BookEditWindow(config, db_obj=db_obj)
            master.top_level_window.wait_visibility()
            master.top_level_window.grab_set()
        else:
            master.top_level_window.focus()

        master.wait_window(master.top_level_window)

    @staticmethod
    @refresh_tables((Book, BookToReader, Reader))
    def delete_book(book: Book):
        confirmation = NotificationWindow(
            title="Подтвердите действие",
            message="Вы уверены, что хотите удалить эту книгу?\n"
                    "При удалении книги, автоматически удалится запись читателей на эту книгу",
            wait_input=False,
            show_cancel=True
        )

        if confirmation.get_input():
            book.delete()
