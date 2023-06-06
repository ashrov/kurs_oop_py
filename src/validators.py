import re


class Validator:
    @staticmethod
    def is_phone_number(str_to_validate: str) -> bool:
        number_pattern = re.compile(r"\+7\d{10}")
        return bool(number_pattern.fullmatch(str_to_validate))

    @staticmethod
    def is_book_count(count: str | int | None) -> bool:
        if isinstance(count, int):
            return count >= 0

        if isinstance(count, str):
            try:
                return int(count) >= 0
            except ValueError:
                return False

        return False
