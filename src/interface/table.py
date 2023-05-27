from typing import Type, TypeVar, Callable, Any
from logging import getLogger

import sqlalchemy as sql
from customtkinter import (
    CTkScrollableFrame, CTkButton, CTkFrame, CTkBaseClass, CTkLabel, CTkFont, CTkEntry, CTkOptionMenu,
    CTkSwitch
)

from ..db import TableViewable, Session, get_database, Sortable
from ..config_models import ConfigModel, ButtonModel
from ..image_manager import ImagesManager


_RowType = TypeVar("_RowType", Type[TableViewable | Sortable], None)

logger = getLogger(__name__)


class RowAction:
    def __init__(self, text: str, command: Callable, image_name: str = None):
        self.text = text
        self.command = command

        self.image_name = image_name

    def get_action_button(self, master: CTkScrollableFrame,
                          button_style: ButtonModel,
                          db_obj: TableViewable = None) -> CTkButton:

        def command():
            if db_obj:
                self.command(db_obj=db_obj)
            else:
                self.command()

        return CTkButton(
            master=master,
            text=self.text,
            command=command,
            image=ImagesManager.get(self.image_name, size=button_style.height - 6) if self.image_name else None,
            **button_style.dict()
        )


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

        self._sortable = issubclass(db_class, Sortable)
        self._sort_with_desc = False

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

        refresh_image = ImagesManager.get("refresh")
        refresh_button = CTkButton(buttons_frame,
                                   text="",
                                   command=lambda: self.refresh(),
                                   image=refresh_image,
                                   width=self._other_buttons_style.height,
                                   height=self._other_buttons_style.height)
        refresh_button.pack(padx=4, pady=4, side="left")

        if self._add_command:
            add_image = ImagesManager.get("add")
            add_button = CTkButton(buttons_frame,
                                   text="Добавить",
                                   command=self._add_command,
                                   image=add_image,
                                   **self._other_buttons_style.dict())
            add_button.pack(padx=4, pady=4, side="left")

        if self._searchable:
            self._create_search_frame(buttons_frame)

        if self._sortable:
            self._create_sort_frame(buttons_frame)

        self._table_frame = CTkScrollableFrame(self)
        self._table_frame.pack(padx=4, pady=(2, 4), fill="both", expand=True)

        self._print_headers()

        self._table_frame.rowconfigure("all", weight=1, pad=4)
        self._table_frame.columnconfigure("all", weight=1, pad=10)

    def _create_search_frame(self, frame: CTkFrame):
        self._search_entry = CTkEntry(frame,
                                      placeholder_text="Введите строку для поиска",
                                      height=self._other_buttons_style.height,
                                      width=200)
        self._search_entry.pack(padx=4, pady=4, side="right")
        self._search_entry.bind("<Return>", self._on_search)

        search_image = ImagesManager.get("search")
        search_button = CTkButton(frame,
                                  text="",
                                  command=self._on_search,
                                  image=search_image,
                                  width=self._other_buttons_style.height,
                                  height=self._other_buttons_style.height)
        search_button.pack(padx=(16, 4), pady=4, side="right")

    def _create_sort_frame(self, frame: CTkFrame):
        self._desc_switch_frame = CTkFrame(frame, width=0, fg_color=frame.cget("fg_color"))
        self._desc_switch_frame.pack(padx=(4, 16), pady=4, side="right")

        up_label = CTkLabel(master=self._desc_switch_frame, text="", image=ImagesManager.get("up"))
        down_label = CTkLabel(master=self._desc_switch_frame, text="", image=ImagesManager.get("down"))

        down_label.pack(side="right", padx=0, pady=0)
        self._desc_switch = CTkSwitch(self._desc_switch_frame,
                                      text="",
                                      command=self._on_sort_desc_switch,
                                      width=0)
        self._desc_switch.pack(padx=0, pady=0, side="right")
        up_label.pack(side="right", padx=0, pady=0)

        order_label = CTkLabel(self._desc_switch_frame, text="Порядок:")
        order_label.pack(side="right", padx=0, pady=0)

        fields = list(self._db_class.get_sort_fields().keys())
        self._sort_box = CTkOptionMenu(frame,
                                       values=fields,
                                       command=self._on_sort_field_select,
                                       height=self._other_buttons_style.height)
        self._sort_box.pack(padx=4, pady=4, side="right")

        self._sort_label = CTkLabel(frame,
                                    text="Сортировать по:")
        self._sort_label.pack(padx=(16, 4), pady=4, side="right")

    def _add_row(self, row: TableViewable):
        row_elements: list[CTkBaseClass] = [CTkLabel(self._table_frame, text=value)
                                            for value in row.get_values().values()]

        if self._row_actions:
            for action in self._row_actions:
                row_elements.append(
                    action.get_action_button(
                        self._table_frame,
                        db_obj=row,
                        button_style=self._in_table_buttons_style
                    )
                )

        for column, element in enumerate(row_elements):
            element.grid(row=len(self._rows) + 1, column=column, padx=4, pady=4)

        self._rows.append(row)
        self._rows_widgets.extend(row_elements)

    def _print_headers(self):
        header_font = CTkFont(weight="bold")

        for column, field in enumerate(self._db_class.get_table_fields()):
            label = CTkLabel(self._table_frame, text=field, font=header_font)
            label.grid(row=0, column=column, padx=10, pady=2)

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

        if self._sortable:
            q = q.order_by(self._get_order_field())

        for row in q.all():
            self._add_row(row)

    def _on_search(self, event=None):
        where_clause = self._db_class.get_search_where_clause(self._search_entry.get())
        self._default_where_clause = where_clause
        self.refresh(where_clause=where_clause)

    def _on_sort_field_select(self, event=None):
        self.refresh()

    def _on_sort_desc_switch(self):
        self._sort_with_desc = self._desc_switch.get()
        self.refresh()

    def _get_order_field(self) -> Any:
        sort_box_choice = self._sort_box.get()
        field = self._db_class.get_sort_fields()[sort_box_choice]

        if self._sort_with_desc:
            field = sql.desc(field)

        return field
