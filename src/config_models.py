""" Модели для парсинга файла конфига """

from pydantic import BaseModel


class DbConfig(BaseModel):
    host: str = "localhost"
    port: int = "3306"
    user: str
    password: str
    database: str

    @property
    def url(self):
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class ButtonModel(BaseModel):
    height: int | None
    width: int | None


class ButtonsStyleModel(BaseModel):
    in_table_buttons: ButtonModel
    other_buttons: ButtonModel


class ConfigModel(BaseModel):
    database: DbConfig
    buttons_style: ButtonsStyleModel
