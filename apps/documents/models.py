from django.db import models


class ParseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    INDEXED = "indexed", "Indexed"
    FAILED = "failed", "Failed"


def candidate_upload_to(instance: "Document", filename: str) -> str:
    return f"candidates/{instance.candidate_id}/{filename}"


class Document(models.Model):
    candidate = models.ForeignKey(
        "candidates.Candidate",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    uploaded_file = models.FileField(upload_to=candidate_upload_to)
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=255, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    parser_name = models.CharField(max_length=100, blank=True)
    parsed_text = models.TextField(blank=True)
    parse_status = models.CharField(
        max_length=20,
        choices=ParseStatus.choices,
        default=ParseStatus.PENDING,
    )
    parser_metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    indexed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.candidate.display_name})"


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    candidate = models.ForeignKey(
        "candidates.Candidate",
        on_delete=models.CASCADE,
        related_name="document_chunks",
    )
    chunk_index = models.PositiveIntegerField()
    chunk_text = models.TextField()
    start_index = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    vector_document_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_id", "chunk_index"]
        unique_together = ("document", "chunk_index")

    def __str__(self) -> str:
        return f"{self.document_id}:{self.chunk_index}"
