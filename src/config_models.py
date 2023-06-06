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


class ConfigModel(BaseModel):
    database: DbConfig
    logging: dict
