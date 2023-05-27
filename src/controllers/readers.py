from typing import Any
from customtkinter import CTkToplevel

from .app_controller import refresh_tables
from .basic_model_controller import BasicModelController
from ..db import BookToReader, Reader, get_database, Session
from ..interface import Table, RowAction, ReaderEditWindow, NotificationWindow, ErrorNotification


class TakenBook(BookToReader):
    @staticmethod
    def get_table_fields() -> list[str]:
        return ["Код", "Название", "Автор"]

    def get_values(self) -> dict[str, Any]:
        return {
            "Код": self.book.code,
            "Название": self.book.name,
            "Автор": self.book.author,
        }


class ReadersController(BasicModelController):
    @classmethod
    def show_taken_books(cls, master, config, db_obj: Reader | None = None):
        table_window = CTkToplevel(width=800, height=400)
        table_window.minsize(800, 400)
        table_window.title("Книги читателя")

        row_actions = [RowAction("Вернуть", command=cls.return_book)]

        table = Table(db_class=TakenBook,
                      config=config,
                      master=table_window,
                      default_where_clause=TakenBook.reader.has(Reader.id == db_obj.id),
                      row_actions=row_actions)
        table.pack(fill="both", expand=True)
        table.refresh()

    @staticmethod
    @refresh_tables()
    def show_edit_window(master, config, db_obj: Reader | None = None):
        edit_window = ReaderEditWindow(config, db_obj=db_obj)
        edit_window.grab_set()
        master.wait_window(edit_window)

    @staticmethod
    @get_database
    @refresh_tables()
    def return_book(db_obj: BookToReader, db: Session = None):
        db.delete(db_obj)
        db.commit()

    @staticmethod
    @refresh_tables((Reader, ))
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
