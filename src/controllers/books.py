from logging import getLogger

from customtkinter import CTkToplevel

from .basic_model_controller import BasicModelController
from .app_controller import refresh_tables
from .tables_controller import TablesController, RowAction
from ..db import (
    Book, wrap_with_database, Session, Reader, BookToReader, add_event_to_history, EventType, History, TakenBook
)
from ..interface import CustomInputDialog, ErrorNotification, NotificationWindow, BookEditWindow
from ..validators import Validator
from ..style_models import StyleConfig


logger = getLogger(__name__)


class BooksController(BasicModelController):
    @classmethod
    def give_book_to_reader(cls, db_object: Book):
        if db_object.get_available_count() <= 0:
            ErrorNotification("Невозможно выдать книгу, так как она отсутствует на складе")
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

        if Validator.is_phone_number(phone_number):
            cls._assign_book_to_reader(db_object, phone_number)
        else:
            ErrorNotification(message="Некорректный номер телефона")
            logger.info(f"incorrect phone number '{phone_number}'")

    @staticmethod
    @refresh_tables((Book, Reader, BookToReader, History))
    @wrap_with_database
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

            add_event_to_history(EventType.BOOK_TAKEN, f"Книга '{book.code}' была выдана читателю '{phone_number}'")

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

    @classmethod
    def show_taken_books(cls, style: StyleConfig, db_obj: Book | None = None):
        table_window = CTkToplevel(width=800, height=400)
        table_window.minsize(800, 400)
        table_window.title("Выданные книги")

        row_actions = (
            RowAction(text="Вернуть", command=BooksController.return_book),
            RowAction(text="Списать", command=BooksController.delete_one_instance_book)
        )

        table = TablesController.create_table(
            db_class=TakenBook,
            style=style,
            master=table_window,
            default_where_clause=TakenBook.reader.has(Book.id == db_obj.id),
            row_actions=row_actions
        )
        table.pack(fill="both", expand=True)
        table.refresh()
        table.grab_set()
        table.master.wait_window(table)

    @staticmethod
    @wrap_with_database
    @refresh_tables()
    def delete_one_instance_book(db_obj: BookToReader, db: Session = None):
        delete_choice = NotificationWindow(
            title="Подтвердите действие",
            message="Вы уверены, что хотите списать данный экземпляр книги?",
            show_cancel=True,
            wait_input=False
        )

        if delete_choice.get_input():
            logger.info(f"Writing off book '{db_obj.book.code}'")

            db.get(Book, db_obj.book_id).count -= 1
            db.delete(db_obj)
            db.commit()

            add_event_to_history(EventType.BOOK_WRITTEN_OFF,
                                 f"Экземпляр книги '{db_obj.book.code}' был списан с читателя '{db_obj.reader.phone}'")

    @staticmethod
    @wrap_with_database
    @refresh_tables((BookToReader, Reader, TakenBook, History))
    def return_book(db_obj: BookToReader, db: Session = None):
        db.delete(db_obj)
        db.commit()

        add_event_to_history(EventType.BOOK_RETURNED,
                             f"Книга '{db_obj.book.code}' была возвращена читателем '{db_obj.reader.phone}'")