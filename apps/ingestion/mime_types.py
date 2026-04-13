from pathlib import Path

import filetype


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"


def detect_mime_type(file_path: str) -> str:
    guessed_kind = filetype.guess(file_path)
    if guessed_kind is not None:
        if guessed_kind.mime == "application/zip" and Path(file_path).suffix.lower() == ".docx":
            return DOCX_MIME
        return guessed_kind.mime

    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return PDF_MIME
    if suffix == ".docx":
        return DOCX_MIME

    return "application/octet-stream"
