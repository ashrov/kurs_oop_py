from dataclasses import dataclass
from datetime import datetime, timedelta

from transliterate import translit
from borb.pdf import SingleColumnLayout, PageLayout, FlexibleColumnWidthTable, Paragraph, Document, Page, PDF
from borb.license.usage_statistics import UsageStatistics

from .db import wrap_with_database, Session, BookToReader, History, EventType, Reader


DAYS_IN_MONTH = 30

UsageStatistics.disable()


@dataclass
class MonthStat:
    new_readers: int = 0
    books_taken: int = 0
    total_readers: int = 0


@wrap_with_database
def _get_month_stat(db: Session = None) -> MonthStat:
    events = db.query(
        History
    ).where(
        History.time >= (datetime.now() - timedelta(days=DAYS_IN_MONTH))
    ).all()

    month_stat = MonthStat()
    for event in events:
        if event.event_type == EventType.NEW_READER:
            month_stat.new_readers += 1
        if event.event_type == EventType.BOOK_TAKEN:
            month_stat.books_taken += 1

    month_stat.total_readers = db.query(Reader).count()

    return month_stat


def _export_to_pdf(data: list[list[str]], filename: str):
    doc: Document = Document()

    page: Page = Page()

    doc.add_page(page)

    layout: PageLayout = SingleColumnLayout(page)

    layout.add(Paragraph("Library month report\n\n", font_size=20))

    month_stat = _get_month_stat()
    layout.add(Paragraph(f"Count of new readers: {month_stat.new_readers}\n"))
    layout.add(Paragraph(f"Count of taken books: {month_stat.books_taken}\n"))
    layout.add(Paragraph(f"Total count of readers: {month_stat.total_readers}\n"))

    layout.add(Paragraph(f"Taken instances of books"))

    table = FlexibleColumnWidthTable(number_of_rows=len(data),
                                     number_of_columns=len(data[0]))
    for line in data:
        for field in line:
            table = table.add(Paragraph(translit(field, "ru", reversed=True)))
    layout.add(table)

    with open(filename, "wb") as pdf_file:
        PDF.dumps(pdf_file, doc)


class PdfCreator:
    @staticmethod
    @wrap_with_database
    def create_pdf_report(filepath: str, db: Session = None):
        data = [("Code", "Name", "Author", "Phone number")]
        for book_to_reader in db.query(BookToReader).all():
            fields = [book_to_reader.book.code, book_to_reader.book.name,
                      book_to_reader.book.author, book_to_reader.reader.phone]
            data.append(fields)
        _export_to_pdf(data, filepath)
