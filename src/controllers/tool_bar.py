from logging import getLogger

from tkinter import filedialog

from .tables_controller import refresh_tables
from ..json_dump import Dumper
from ..pdf_report import PdfCreator
from ..wrappers import log_it


logger = getLogger(__name__)


class ToolBarController:
    @staticmethod
    @log_it(logger=logger)
    def on_dump():
        filename = filedialog.asksaveasfilename(title="Choose file for dump",
                                                defaultextension=".json",
                                                filetypes=[("Json file", ".json"), ("Text file", ".txt")])
        if filename:
            Dumper.dump_to_file(filename)

    @staticmethod
    @refresh_tables()
    @log_it(logger=logger)
    def on_load():
        filename = filedialog.askopenfilename(title="Choose dump file to import",
                                              defaultextension=".json",
                                              filetypes=[("Json file", ".json"), ("Text file", ".txt")])
        if filename:
            Dumper.load_from_file(filename)

    @staticmethod
    @log_it(logger=logger)
    def on_pdf_report():
        filename = filedialog.asksaveasfilename(title="Saving pdf report",
                                                defaultextension=".pdf",
                                                filetypes=[("PDF file", ".pdf")])
        if filename:
            PdfCreator.create_pdf_report(filename)
