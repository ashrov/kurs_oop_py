import re

from .exc import FieldValidationError


class Validator:
    """ Класс для валидации различных данных """

    @staticmethod
    def validate_phone_number(str_to_validate: str) -> None:
        number_pattern = re.compile(r"\+7\d{10}")

        if not number_pattern.fullmatch(str_to_validate):
            raise FieldValidationError("Некорректный номер телефона")

    @staticmethod
    def validate_book_count(count: str | int | None, taken: int) -> None:
        if isinstance(count, int):
            if count < taken:
                raise FieldValidationError("Количество книг не может быть меньше, чем количество уже взятых книг.\n"
                                           f"Взято данных книг: {taken}.")

        if isinstance(count, str):
            try:
                Validator.validate_book_count(int(count), taken)
            except ValueError:
                raise FieldValidationError("Количество книг должно быть числом")
