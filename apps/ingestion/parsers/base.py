from dataclasses import dataclass


@dataclass(slots=True)
class ParsedDocument:
    text: str
    metadata: dict


class BaseDocumentParser:
    parser_name = "base"

    def parse(self, file_path: str) -> ParsedDocument:
        raise NotImplementedError
