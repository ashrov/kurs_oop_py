from pathlib import Path

from PIL import Image
from customtkinter import CTkImage


IMAGES_DIR = "./images"


class ImagesManager:
    @staticmethod
    def get(image_name: str, size: int = 20) -> CTkImage:
        image_file = f"{image_name}.png"
        image_path = Path(IMAGES_DIR).joinpath(image_file)

        image = CTkImage(dark_image=Image.open(image_path),
                         size=(size, size))

        return image
