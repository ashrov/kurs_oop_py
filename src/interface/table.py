from typing import Type, TypeVar, Callable, Any
from logging import getLogger

from customtkinter import CTkScrollableFrame, CTkButton, CTkFrame, CTkBaseClass, CTk, CTkLabel, CTkFont, CTkEntry

from ..db import TableViewable, Session, get_database
from ..config_models import ConfigModel


_RowType = TypeVar("_RowType", Type[TableViewable], None)

logger = getLogger(__name__)


class RowAction:
    def __init__(self, text: str, command: Callable):
        self.text = text
        self.command = command

    def get_action_button(self, master: CTkBaseClass, button_style: dict, db_obj: TableViewable = None) -> CTkButton:
        command = lambda: self.command(db_obj=db_obj) if db_obj else self.command
        return CTkButton(master=master, text=self.text, command=command, **button_style)


class Table(CTkFrame):
    def __init__(self,
                 db_class: _RowType,
                 config: ConfigModel,
                 master: Any,
                 *args,
                 searchable: bool = True,
                 row_actions: list[RowAction] = None,
                 add_command: Callable = None,
                 default_where_clause: Any = None,
                 **kwargs):

        super().__init__(*args, master=master, **kwargs)

        self._db_class = db_class
        self._add_command = add_command
        self._row_actions = row_actions
        self._default_where_clause = default_where_clause
        self._searchable = searchable
        self._config = config
        self._in_table_buttons_style = config.buttons_style.in_table_buttons
        self._other_buttons_style = config.buttons_style.other_buttons

        self._rows: list[db_class] = list()
        self._rows_widgets: list[CTkBaseClass] = list()

        self._create_widgets()

    def get_db_class(self):
        return self._db_class

    def set_default_where_clause(self, where_clause: Any):
        self._default_where_clause = where_clause

    def _create_widgets(self):
        buttons_frame = CTkFrame(self)
        buttons_frame.pack(pady=(4, 2), padx=4, side="top", fill="x")

        refresh_button = CTkButton(buttons_frame,
                                   text="Обновить",
                                   command=lambda: self.refresh(),
                                   **self._other_buttons_style.dict())
        refresh_button.pack(padx=4, pady=4, side="left")

        if self._add_command:
            add_button = CTkButton(buttons_frame,
                                   text="Добавить",
                                   command=self._add_command,
                                   **self._other_buttons_style.dict())
            add_button.pack(padx=4, pady=4, side="left")

        if self._searchable:
            self._search_entry = CTkEntry(buttons_frame,
                                          placeholder_text="Введите строку для поиска",
                                          height=self._other_buttons_style.height,
                                          width=200)
            self._search_entry.pack(padx=4, pady=4, side="right")
            self._search_entry.bind("<Return>", self._on_search)

            search_button = CTkButton(buttons_frame,
                                      text="Поиск",
                                      command=self._on_search,
                                      **self._other_buttons_style.dict())
            search_button.pack(padx=4, pady=4, side="right")

        self._table_frame = CTkScrollableFrame(self)
        self._table_frame.pack(padx=4, pady=(2, 4), fill="both", expand=True)

        self._print_headers()

        self._table_frame.rowconfigure("all", weight=1, pad=4)
        self._table_frame.columnconfigure("all", weight=1, pad=10)

    def _add_row(self, row: TableViewable):
        row_elements: list[CTkBaseClass] = [CTkLabel(self._table_frame, text=value)
                                            for value in row.get_values().values()]

        if self._row_actions:
            for action in self._row_actions:
                row_elements.append(
                    action.get_action_button(
                        self._table_frame,
                        db_obj=row,
                        button_style=self._in_table_buttons_style.dict()
                    )
                )

        for column, element in enumerate(row_elements):
            element.grid(row=len(self._rows) + 1, column=column, padx=10, pady=4)

        self._rows.append(row)
        self._rows_widgets.extend(row_elements)

    def _print_headers(self):
        header_font = CTkFont(weight="bold")

        for column, field in enumerate(self._db_class.get_table_fields()):
            label = CTkLabel(self._table_frame, text=field, font=header_font)
            label.grid(row=0, column=column, padx=10)

    def clear(self):
        self._rows.clear()

        for widget in self._rows_widgets:
            widget.destroy()
        self._rows_widgets.clear()

    def refresh(self, where_clause: Any = None):
        logger.info(f"Refreshing '{self._db_class.get_table_name()}' table with where_clause='{where_clause}'")
        self.clear()

        self.after(5, lambda: self._fill_from_database(where_clause))

    @get_database
    def _fill_from_database(self, where_clause: Any = None, db: Session = None):
        q = db.query(self._db_class)
        if self._default_where_clause is not None:
            q = q.where(self._default_where_clause)
        if where_clause is not None:
            q = q.where(where_clause)

        for row in q.all():
            self._add_row(row)

    def _on_search(self, event=None):
        where_clause = self._db_class.get_search_where_clause(self._search_entry.get())
        self.refresh(where_clause=where_clause)
