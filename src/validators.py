import re


class Validator:
    @staticmethod
    def is_phone_number(str_to_validate: str) -> bool:
        number_pattern = re.compile(r"\+7\d{10}")
        return bool(number_pattern.fullmatch(str_to_validate))
