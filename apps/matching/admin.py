from django.contrib import admin

from .models import CandidateMatch, JobRequest


class CandidateMatchInline(admin.TabularInline):
    model = CandidateMatch
    extra = 0
    readonly_fields = ("candidate", "rank", "retrieval_score", "fit_score", "final_score")


@admin.register(JobRequest)
class JobRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "top_k", "retrieval_k", "created_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("title", "description_text")
    inlines = [CandidateMatchInline]
