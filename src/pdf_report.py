import itertools
from random import randint
from statistics import mean

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .db import get_database, Session, Book


def _grouper(iterable, n):
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args)


def _export_to_pdf(data, filepath):
    c = Canvas(filepath, pagesize=A4)
    pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf'))
    c.setFont('FreeSans', 16)
    w, h = A4
    max_rows_per_page = 40

    c.drawString(50, h - 50, "Отчёт")

    c.setFont('FreeSans', 8)

    x_offset = 50
    y_offset = 80

    padding = 15

    xlist = [x + x_offset for x in [0, 50, 220, 380, 460, 500]]
    ylist = [h - y_offset - i * padding for i in range(max_rows_per_page + 1)]

    for rows in _grouper(data, max_rows_per_page):
        rows = tuple(filter(bool, rows))
        c.grid(xlist, ylist[:len(rows) + 1])
        for y, row in zip(ylist[:-1], rows):
            for x, cell in zip(xlist, row):
                c.drawString(x + 2, y - padding + 3, str(cell))
        c.showPage()

    c.save()


@get_database
def create_pdf_report(filepath: str, db: Session = None):
    data = [("Код книги", "Название", "Автор", "Сейчас доступно", "Всего")]
    for book in db.query(Book).all():
        data.append((book.code, book.name, book.author, book.get_available_count(), book.count))
    _export_to_pdf(data, filepath)
