from customtkinter import CTkToplevel, CTkLabel, CTkButton, CTk


class NotificationWindow(CTkToplevel):
    def __init__(self, master: CTk, message: str):
        super().__init__(master)

        self._result = None

        self.resizable(False, False)

        self._message_label = CTkLabel(self, text=message)
        self._message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        self._ok_button = CTkButton(self, text="Ok", command=self._ok_event)
        self._ok_button.grid(row=2, column=0, columnspan=1, padx=(20, 10), pady=(0, 20), sticky="ew")
        self._cancel_button = CTkButton(self, text="Cancel", command=self._cancel_event)
        self._cancel_button.grid(row=2, column=1, columnspan=1, padx=(10, 20), pady=(0, 20), sticky="ew")

        self.after(150, lambda: self.focus())  # set focus to entry with slight delay, otherwise it won't work
        self._ok_button.bind("<Return>", self._ok_event)

    def _ok_event(self):
        self._result = True
        self.grab_release()
        self.destroy()

    def _cancel_event(self):
        self._result = False
        self.grab_release()
        self.destroy()

    def get_input(self):
        return self._result

