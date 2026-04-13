from django.contrib import admin

from .models import Document, DocumentChunk


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    readonly_fields = ("chunk_index", "start_index", "vector_document_id", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "candidate",
        "original_filename",
        "mime_type",
        "parse_status",
        "indexed_at",
        "created_at",
    )
    list_filter = ("parse_status", "mime_type")
    search_fields = ("original_filename", "candidate__first_name", "candidate__last_name")
    readonly_fields = ("sha256", "parser_name", "parser_metadata", "indexed_at")
    inlines = [DocumentChunkInline]
