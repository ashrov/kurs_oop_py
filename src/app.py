from typing import Any, Type, TypeVar
from logging import getLogger, DEBUG, INFO

from tkinter import StringVar, filedialog
from customtkinter import set_default_color_theme, set_appearance_mode, \
    CTk, CTkButton, CTkTabview, CTkLabel, CTkFrame, CTkToplevel, CTkEntry

from .db import TableViewable, Book, Reader, Session, get_database
from .interface import CustomInputDialog, Table, RowAction
from .config_models import ConfigModel
from .json_dump import Dumper
from .pdf_report import create_pdf_report
from .wrappers import log_it


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500


logger = getLogger(__name__)

_RowType = TypeVar("_RowType", Type[TableViewable], None)


class BaseEditWindow(CTkToplevel):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app

        self._rows_frame = CTkFrame(self)
        self._rows_frame.pack()
        self._rows_count = 0

    def _add_field_row(self, name: str, value: Any) -> CTkEntry:
        label = CTkLabel(self._rows_frame, text=name)
        label.grid(row=self._rows_count, column=0, padx=10, pady=2)

        str_var = StringVar(self, value=value)
        entry = CTkEntry(self._rows_frame, textvariable=str_var)
        entry.grid(row=self._rows_count, column=1, padx=10, pady=2)

        self._rows_count += 1

        return entry

    def _add_custom_field_row(self, obj):
        obj.grid(row=self._rows_count, column=1)
        self._rows_count += 1

    def _get_rows_frame(self):
        return self._rows_frame


class BookEditWindow(BaseEditWindow):
    def __init__(self, *args, db_obj: Book = None, **kwargs):
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

    def add_bottom_buttons(self):
        buttons_frame = CTkFrame(self)

        save_button = CTkButton(buttons_frame, text="Сохранить", command=self.save)
        save_button.pack(side="right")

        buttons_frame.pack(side="bottom")

    @get_database
    def save(self, db: Session):
        self._book.code = self._code_entry.get()
        self._book.name = self._name_entry.get()
        self._book.author = self._author_entry.get()
        self._book.count = self._count_entry.get()

        db.add(self._book)
        db.commit()

        self.destroy()


def show_edit_window(master, db_obj: Book | None = None):
    if isinstance(db_obj, Book):
        if not master.top_level_window or not master.top_level_window.winfo_exists():
            master.top_level_window = BookEditWindow(master, db_obj=db_obj)
            master.top_level_window.wait_visibility()
            master.top_level_window.grab_set()
        else:
            master.top_level_window.focus()


def give_book_to_reader(master, db_object: Book):
    phone_number = CustomInputDialog(title="Выдача книги", text="Введите номер телефона читателя")
    print(phone_number.get_input())


class CustomTabView(CTkTabview):
    def __init__(self, app: "Application", config: ConfigModel, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._config = config

        self._app = app
        self.tables: list[Table] = list()

    def add(self, db_class: _RowType, *args, **kwargs) -> CTkFrame:
        tab_frame = super().add(db_class.get_table_name())

        table = Table(*args,
                      config=self._config,
                      app=self._app,
                      db_class=db_class,
                      master=tab_frame,
                      height=WINDOW_HEIGHT,
                      **kwargs)
        table.pack(padx=10, fill="both")
        table.refresh()

        self.tables.append(table)

        return tab_frame

    def refresh(self):
        for table in self.tables:
            table.refresh()


class Application(CTk):
    def __init__(self, config: ConfigModel):
        super().__init__()

        self._config = config
        self._buttons_style = config.buttons_style.other_buttons
        self.top_level_window = None

        logger.debug("Creating interface")

        set_default_color_theme("dark-blue")
        set_appearance_mode("dark")
        self.title("Library Manager")
        self.minsize(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

        self._create_dump_menu()

        self.tab_view = CustomTabView(self, config)
        self.tab_view.pack(padx=10, fill="both")

        book_actions = [
            RowAction("Выдать", command=lambda db_obj: give_book_to_reader(self, db_obj)),
            RowAction("Изменить", command=lambda db_obj: show_edit_window(self, db_obj)),
            RowAction("Удалить", command=lambda db_obj: db_obj.delete())
        ]
        self.tab_view.add(Book, row_actions=book_actions, add_command=lambda: show_edit_window(self, Book()))
        self.tab_view.add(Reader)

    def _create_dump_menu(self):

        @log_it(logger=logger)
        def on_dump():
            filename = filedialog.asksaveasfilename(title="Choose file for dump",
                                                    defaultextension=".json",
                                                    filetypes=[("Json file", ".json"), ("Text file", ".txt")])
            if filename:
                Dumper.dump_to_file(filename)

        @log_it(logger=logger)
        def on_load():
            filename = filedialog.askopenfilename(title="Choose dump file to import",
                                                  defaultextension=".json",
                                                  filetypes=[("Json file", ".json"), ("Text file", ".txt")])
            if filename:
                Dumper.load_from_file(filename)

        @log_it(logger=logger)
        def on_pdf_report():
            filename = filedialog.asksaveasfilename(title="Saving pdf report",
                                                    defaultextension=".pdf",
                                                    filetypes=[("PDF file", ".pdf")])
            if filename:
                create_pdf_report(filename)

        bar_frame = CTkFrame(self)
        bar_frame.pack(pady=4, padx=4, fill="x")

        import_button = CTkButton(bar_frame,
                                  text="Импорт",
                                  **self._buttons_style.dict(),
                                  command=on_load)
        import_button.pack(side="left", padx=4, pady=4)

        export_button = CTkButton(bar_frame,
                                  text="Экспорт",
                                  **self._buttons_style.dict(),
                                  command=on_dump)
        export_button.pack(side="left", padx=4, pady=4)

        pdf_report_button = CTkButton(bar_frame,
                                      text="PDF отчёт",
                                      **self._buttons_style.dict(),
                                      command=on_pdf_report)
        pdf_report_button.pack(side="left", padx=4, pady=4)
