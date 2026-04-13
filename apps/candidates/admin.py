from django.contrib import admin

from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "headline", "created_at")
    search_fields = ("first_name", "last_name", "email", "headline")
