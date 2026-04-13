from django.shortcuts import render

from apps.documents.models import Document
from apps.matching.models import JobRequest


def dashboard(request):
    context = {
        "recent_documents": Document.objects.select_related("candidate")[:10],
        "recent_job_requests": JobRequest.objects.prefetch_related("matches__candidate")[:10],
    }
    return render(request, "ui/index.html", context)
