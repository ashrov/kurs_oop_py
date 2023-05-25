from typing import Any
from abc import ABC, abstractmethod
from enum import Enum
from logging import getLogger

from tkinter import StringVar
from customtkinter import CTkToplevel, CTk, CTkFrame, CTkEntry, CTkLabel, CTkButton

from ..notificate import NotificationWindow, ErrorNotification
from src.exc import EmptyFieldError, ModelEditError


logger = getLogger(__name__)


class EditResult(Enum):
    NEW = 1
    EDITED = 0
    CANCELED = 0


class BaseEditWindow(CTkToplevel, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resizable(False, False)

        self.edit_result: EditResult | None = None

        self._rows_frame = CTkFrame(self)
        self._rows_frame.pack(pady=(10, 5), padx=10, fill="x")
        self._rows_count = 0

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    @staticmethod
    def process_field(entry: CTkEntry, not_empty: bool = True) -> str | None:
        value = entry.get() or None

        if not_empty and not value:
            raise EmptyFieldError("Ошибка, пропущено обязательное поле")

        return value

    def add_bottom_buttons(self):
        buttons_frame = CTkFrame(self)

        save_button = CTkButton(buttons_frame, text="Сохранить", command=self._try_save)
        save_button.pack(side="left", pady=10, padx=10)

        cancel_button = CTkButton(buttons_frame, text="Отменить", command=self._on_cancel)
        cancel_button.pack(side="right", pady=10, padx=10)

        buttons_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 10))

    def _on_cancel(self):
        self.edit_result = EditResult.CANCELED
        self.grab_release()
        self.destroy()

    def _add_field_row(self, name: str, value: Any) -> CTkEntry:
        label = CTkLabel(self._rows_frame, text=name)
        label.grid(row=self._rows_count, column=0, padx=10, pady=2)

        str_var = StringVar(self, value=value)
        entry = CTkEntry(self._rows_frame, textvariable=str_var, width=210)
        entry.grid(row=self._rows_count, column=1, padx=10, pady=2)

        self._rows_count += 1

        return entry

    def _add_custom_field_row(self, obj):
        obj.grid(row=self._rows_count, column=1)
        self._rows_count += 1

    def _get_rows_frame(self):
        return self._rows_frame

    def _try_save(self):
        try:
            self.save()
        except ModelEditError as e:
            logger.exception("Exception while save model")
            ErrorNotification(message=e.args[0])

        self.destroy()

    @abstractmethod
    def save(self):
        ...


