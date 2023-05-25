from typing import Any
from customtkinter import CTkToplevel, CTkLabel, CTk, CTkProgressBar


class ProgressBarWindow(CTkToplevel):
    def __init__(self, master: Any, title: str, stages: list[str] | None):
        super().__init__(master)

        self.resizable(False, False)
        self.title(title)

        if not stages:
            stages = [title]

        self._stages = stages
        self._cur_stage = 0

        self._label = CTkLabel(self, text=stages[0])
        self._label.pack(side="top", pady=20, padx=20)

        self._progress_bar = CTkProgressBar(self, mode="determinate", determinate_speed=0)
        self._progress_bar.set(0)
        self._progress_bar.pack(side="top", pady=20, padx=20)
        self._progress_bar.start()
        self.master.grab_release()
        self.wait_visibility()
        self.grab_set()
        self.lift()

    def next(self):
        if self._cur_stage + 1 < len(self._stages):
            self._cur_stage += 1
            self._update()
        else:
            self.stop()

    def stop(self):
        self.grab_release()
        self.destroy()

    def _update(self):
        self._label.configure(text=self._stages[self._cur_stage])
        self._progress_bar.set(self._cur_stage / len(self._stages))
