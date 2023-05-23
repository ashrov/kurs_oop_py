from customtkinter import CTkInputDialog


class CustomInputDialog(CTkInputDialog):
    def __init__(self, *args, **kwargs):
        """
        Класс для исправления недочёта в библиотеке customtkinter
        (в классе CTkInputDialog при нажатии на ok и cancel используется один обработчик,
        в результате чего при нажатии на любую кнопку вернётся ввод, т.е. кнопка отмены не имеет смысла)
        """

        super().__init__(*args, **kwargs)

        self.after(40, lambda: self._cancel_button.configure(command=self._cancel_event))
