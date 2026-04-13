from pypdf import PdfReader

from .base import BaseDocumentParser, ParsedDocument


class PdfDocumentParser(BaseDocumentParser):
    parser_name = "pypdf"

    def parse(self, file_path: str) -> ParsedDocument:
        reader = PdfReader(file_path)
        pages: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())

        text = "\n\n".join(pages)
        return ParsedDocument(
            text=text,
            metadata={
                "page_count": len(reader.pages),
                "pages_with_text": len(pages),
                "parser": self.parser_name,
            },
        )
