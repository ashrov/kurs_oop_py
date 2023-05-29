from transliterate import translit

from borb.pdf import SingleColumnLayout
from borb.pdf import PageLayout
from borb.pdf import FlexibleColumnWidthTable
from borb.pdf import Paragraph
from borb.pdf import Document
from borb.pdf import Page
from borb.pdf import PDF

from .db import get_database, Session, Book


def _export_to_pdf(data: list[list[str]], filename: str):
    doc: Document = Document()

    page: Page = Page()

    doc.add_page(page)

    # set a PageLayout
    layout: PageLayout = SingleColumnLayout(page)

    table = FlexibleColumnWidthTable(number_of_rows=len(data),
                                     number_of_columns=len(data[0]))
    for line in data:
        for field in line:
            table = table.add(Paragraph(translit(field, "ru", reversed=True)))
    layout.add(table)

    with open(filename, "wb") as pdf_file:
        PDF.dumps(pdf_file, doc)


@get_database
def create_pdf_report(filepath: str, db: Session = None):
    data = [("Code", "Name", "Author", "Available", "Total")]
    for book in db.query(Book).all():
        fields = [book.code, book.name, book.author, str(book.get_available_count()), str(book.count)]
        fields = [translit(field, "ru", reversed=True) for field in fields]
        data.append(fields)
    _export_to_pdf(data, filepath)
