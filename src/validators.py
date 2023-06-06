import re


class Validator:
    @staticmethod
    def is_phone_number(str_to_validate: str) -> bool:
        number_pattern = re.compile(r"\+7\d{10}")
        return bool(number_pattern.fullmatch(str_to_validate))

    @staticmethod
    def is_book_count(field_to_validate: str | int | None) -> bool:
        if isinstance(field_to_validate, int):
            return field_to_validate >= 0
        if isinstance(field_to_validate, str):
            try:
                return int(field_to_validate) >= 0
            except ValueError:
                return False
        return False
