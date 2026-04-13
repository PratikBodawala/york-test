from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.ui.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("apps.candidates.urls")),
    path("api/", include("apps.matching.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
