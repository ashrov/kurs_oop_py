from pydantic import BaseModel


class ButtonStyle(BaseModel):
    height: int
    width: int


class StyleConfig(BaseModel):
    in_table_buttons: ButtonStyle
    other_buttons: ButtonStyle
