from typing import Type, TypeVar, Iterable
from logging import getLogger

from sqlalchemy.exc import OperationalError
from customtkinter import set_default_color_theme, set_appearance_mode, \
    CTk, CTkButton, CTkTabview, CTkFrame, CTkProgressBar

from .db import TableViewable, Book, Reader, BookToReader, History, init_db
from .interface import RowAction, ProgressBarWindow, ErrorNotification
from .config_models import ConfigModel
from .controllers import BooksController, ToolBarController, ReadersController, TablesController


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 500


logger = getLogger(__name__)

_RowType = TypeVar("_RowType", Type[TableViewable], None)


class CustomTabView(CTkTabview):
    def __init__(self, config: ConfigModel, *args, **kwargs):
        self._button_height = 32
        super().__init__(*args, **kwargs)

        self._config = config

    def add(self, db_class: _RowType, *args, **kwargs) -> CTkFrame:
        tab_frame = super().add(db_class.get_table_name())

        table = TablesController.create_table(
            *args,
            config=self._config,
            db_class=db_class,
            master=tab_frame,
            height=WINDOW_HEIGHT,
            **kwargs
        )

        table.pack(padx=10, fill="both", expand=True)

        return tab_frame


class Application(CTk):
    def __init__(self, config: ConfigModel):
        super().__init__()

        self._config = config

        set_default_color_theme("dark-blue")
        set_appearance_mode("dark")

        self.title("Library Manager")
        self.minsize(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

        self.after(20, self._create_progress_bar)

        self.after(200, self._create_widgets)

    def _create_progress_bar(self):
        self._loading_progress = ProgressBarWindow(self, "Загрузка", ["Инициализация графических элементов",
                                                                      "Инициализация подключения к базе данных",
                                                                      "Загрузка данных"])

    def _connect_to_db(self):
        try:
            logger.info("Connecting to database")
            init_db(self._config.database)
            self._loading_progress.next()
            TablesController.refresh()
            self.after(500, self._loading_progress.stop)
        except OperationalError as e:
            logger.exception("Unable to connect to database", exc_info=True)
            self._loading_progress.stop()
            ErrorNotification("Невозможно подключиться к базе данных.\n"
                              f"Ошибка: {e.args}")

            self.destroy()

    def _create_widgets(self):
        self._loading_progress.next()

        self._buttons_style = self._config.buttons_style.other_buttons
        self.top_level_window = None

        logger.debug("Creating interface")

        self._create_dump_menu()

        self.tab_view = CustomTabView(master=self, config=self._config)
        self.tab_view.pack(padx=10, pady=10, fill="both", expand=True)

        book_actions = [
            RowAction(text="Посмотреть выданные",
                      command=lambda db_obj: BooksController.show_taken_books(self._config, db_obj)),
            RowAction(text="Выдать",
                      command=lambda db_obj: BooksController.give_book_to_reader(self, db_obj)),
            RowAction(command=lambda db_obj: BooksController.show_edit_window(self, self._config, db_obj),
                      image_name="edit"),
            RowAction(command=lambda db_obj: BooksController.delete_book(db_obj),
                      image_name="delete")
        ]
        self.tab_view.add(Book,
                          row_actions=book_actions,
                          add_command=lambda: BooksController.show_edit_window(self, self._config))

        reader_actions = [
            RowAction(text="Выданные книги",
                      command=lambda db_obj: ReadersController.show_taken_books(self._config, db_obj)),
            RowAction(command=lambda db_obj: ReadersController.show_edit_window(self, self._config, db_obj),
                      image_name="edit"),
            RowAction(command=lambda db_obj: ReadersController.delete_reader(db_obj),
                      image_name="delete")
        ]
        self.tab_view.add(Reader,
                          row_actions=reader_actions,
                          add_command=lambda: ReadersController.show_edit_window(self, self._config))

        book_to_reader_actions = [
            RowAction(text="Вернуть", command=ReadersController.return_book)
        ]
        self.tab_view.add(BookToReader,
                          row_actions=book_to_reader_actions)

        self.tab_view.add(History, searchable=False)

        self._loading_progress.next()
        self.after(100, self._connect_to_db)

    def _create_dump_menu(self):
        bar_frame = CTkFrame(self)
        bar_frame.pack(pady=10, padx=10, fill="x")

        import_button = CTkButton(bar_frame,
                                  text="Импорт",
                                  **self._buttons_style.dict(),
                                  command=ToolBarController.on_load)
        import_button.pack(side="left", padx=4, pady=4)

        export_button = CTkButton(bar_frame,
                                  text="Экспорт",
                                  **self._buttons_style.dict(),
                                  command=ToolBarController.on_dump)
        export_button.pack(side="left", padx=4, pady=4)

        pdf_report_button = CTkButton(bar_frame,
                                      text="PDF отчёт",
                                      **self._buttons_style.dict(),
                                      command=ToolBarController.on_pdf_report)
        pdf_report_button.pack(side="left", padx=4, pady=4)
