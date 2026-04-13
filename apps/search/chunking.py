from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_chunks(document_text: str, metadata: dict) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    source_document = Document(page_content=document_text, metadata=metadata)
    return splitter.split_documents([source_document])
