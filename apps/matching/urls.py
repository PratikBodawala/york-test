from django.urls import path

from .views import create_match_request, match_status


urlpatterns = [
    path("matches/", create_match_request, name="create-match-request"),
    path("matches/<int:job_request_id>/", match_status, name="match-status"),
]
