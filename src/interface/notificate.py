from customtkinter import CTkToplevel, CTkLabel, CTkButton, CTk


class NotificationWindow(CTkToplevel):
    def __init__(self,
                 title: str = "Notification",
                 message: str = "Notification",
                 show_cancel: bool = False,
                 wait_input: bool = True):

        super().__init__()

        self._title = title
        self._message = message
        self._show_cancel = show_cancel
        self._wait_input = wait_input

        self._result: bool | None = None

        self._create_widgets()

        self.lift()
        self.attributes("-topmost", True)  # stay on top
        self.protocol("WM_DELETE_WINDOW", self._cancel_event)
        self.after(10, self._create_widgets)
        self.grab_set()

        if self._wait_input:
            self.master.wait_window(self)

    def _create_widgets(self):
        self.title(self._title)
        self.resizable(False, False)

        self._message_label = CTkLabel(self, text=self._message)
        self._message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        ok_col_span = 1 if self._show_cancel else 2
        ok_padx = (20, 10) if self._show_cancel else (20, 20)

        self._ok_button = CTkButton(self, text="Ok", command=self._ok_event)
        self._ok_button.grid(row=2, column=0, columnspan=ok_col_span, padx=ok_padx, pady=(0, 20), sticky="ew")

        if self._show_cancel:
            self._cancel_button = CTkButton(self, text="Cancel", command=self._cancel_event)
            self._cancel_button.grid(row=2, column=1, columnspan=1, padx=(10, 20), pady=(0, 20), sticky="ew")

        self.after(100, lambda: self._ok_button.focus)  # set focus to entry with slight delay, otherwise it won't work
        self._ok_button.bind("<Return>", self._ok_event)

    def _ok_event(self):
        self._result = True
        self.grab_release()
        self.destroy()

    def _cancel_event(self):
        self._result = False
        self.grab_release()
        self.destroy()

    def get_input(self) -> bool | None:
        if not self._wait_input:
            self.master.wait_window(self)
        return self._result


class ErrorNotification(NotificationWindow):
    def __init__(self, message: str):
        super().__init__(title="Ошибка",
                         message=message,
                         show_cancel=False)
