from customtkinter import CTkToplevel

from .books import BooksController
from .tables_controller import TablesController, refresh_tables
from ..db import BookToReader, Reader, wrap_with_database, Session, add_event_to_history, EventType, History, TakenBook
from ..interface import RowAction, ReaderEditWindow, NotificationWindow, ErrorNotification
from ..style_models import StyleConfig


class ReadersController:
    @staticmethod
    def show_taken_books(style: StyleConfig, db_obj: Reader | None = None):
        table_window = CTkToplevel(width=800, height=400)
        table_window.minsize(800, 400)
        table_window.title("Книги читателя")

        row_actions = (
            RowAction(text="Вернуть", command=BooksController.return_book),
            RowAction(text="Списать", command=BooksController.delete_one_instance_book)
        )

        table = TablesController.create_table(
            db_class=TakenBook,
            style=style,
            master=table_window,
            default_where_clause=TakenBook.reader.has(Reader.id == db_obj.id),
            row_actions=row_actions
        )
        table.pack(fill="both", expand=True)
        table.refresh()
        table.grab_set()
        table.master.wait_window(table)

    @staticmethod
    @refresh_tables((Reader, BookToReader, History))
    def show_edit_window(master, db_obj: Reader | None = None):
        edit_window = ReaderEditWindow(db_obj=db_obj)
        master.wait_window(edit_window)

    @staticmethod
    @refresh_tables((Reader, History))
    @wrap_with_database
    def delete_reader(reader: Reader, db: Session = None):
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
            db.delete(reader)
            db.commit()
            add_event_to_history(EventType.READER_LEFT, f"Читатель '{reader.phone}' был удалён из базы данных")
