from typing import Any
from customtkinter import CTkToplevel

from .app_controller import refresh_tables
from .basic_model_controller import BasicModelController
from .tables_controller import TablesController
from ..db import BookToReader, Reader, wrap_with_database, Session, add_event_to_history, EventType, History, TakenBook
from ..interface import RowAction, ReaderEditWindow, NotificationWindow, ErrorNotification


class ReadersController(BasicModelController):
    @classmethod
    def show_taken_books(cls, config, db_obj: Reader | None = None):
        table_window = CTkToplevel(width=800, height=400)
        table_window.minsize(800, 400)
        table_window.title("Книги читателя")

        row_actions = [RowAction(text="Вернуть", command=cls.return_book)]

        table = TablesController.create_table(
            db_class=TakenBook,
            config=config,
            master=table_window,
            default_where_clause=TakenBook.reader.has(Reader.id == db_obj.id),
            row_actions=row_actions
        )
        table.pack(fill="both", expand=True)
        table.refresh()
        table.master.wait_window(table)

    @staticmethod
    @refresh_tables((Reader, BookToReader, History))
    def show_edit_window(master, config, db_obj: Reader | None = None):
        edit_window = ReaderEditWindow(config, db_obj=db_obj)
        edit_window.grab_set()
        master.wait_window(edit_window)

    @staticmethod
    @wrap_with_database
    @refresh_tables((BookToReader, Reader, TakenBook, History))
    def return_book(db_obj: BookToReader, db: Session = None):
        db.delete(db_obj)
        db.commit()

        add_event_to_history(EventType.BOOK_RETURNED,
                             f"Книга '{db_obj.book.code}' была возвращена читателем '{db_obj.reader.phone}'")

    @staticmethod
    @refresh_tables((Reader, History))
    def delete_reader(reader: Reader):
        if len(reader.books_associations):
            ErrorNotification("Невозможно удалить читателя, пока на него записана хотя бы одна книга")
            return

        confirmation = NotificationWindow(
            title="Подтвердите действие",
            message="Вы уверены, что хотите удалить этого читателя'?",
            wait_input=False,
            show_cancel=True
        )

        if confirmation.get_input():
            reader.delete()
            add_event_to_history(EventType.READER_LEFT, f"Читатель '{reader.phone}' был удалён из базы данных")
