from apps.ingestion.mime_types import DOCX_MIME, PDF_MIME

from .base import BaseDocumentParser
from .docx import DocxDocumentParser
from .pdf import PdfDocumentParser


class UnsupportedMimeTypeError(ValueError):
    pass


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, BaseDocumentParser] = {
            PDF_MIME: PdfDocumentParser(),
            DOCX_MIME: DocxDocumentParser(),
        }

    def get_parser(self, mime_type: str) -> BaseDocumentParser:
        parser = self._parsers.get(mime_type)
        if parser is None:
            raise UnsupportedMimeTypeError(f"Unsupported MIME type: {mime_type}")
        return parser


parser_registry = ParserRegistry()
