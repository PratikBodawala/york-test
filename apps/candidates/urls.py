from django.urls import path

from .views import document_status, upload_candidate_resume


urlpatterns = [
    path("candidates/upload/", upload_candidate_resume, name="upload-candidate-resume"),
    path("documents/<int:document_id>/", document_status, name="document-status"),
]
