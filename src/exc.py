class ModelEditError(Exception):
    pass


class EmptyFieldError(ModelEditError):
    pass


class FieldValidationError(ModelEditError):
    pass
