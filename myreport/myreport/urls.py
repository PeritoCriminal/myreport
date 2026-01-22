from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls", namespace="home")),
    path("accounts/", include("accounts.urls")),
    path("rede/", include("social_net.urls")),
    path("grupos/", include("groups.urls", namespace="groups")),
    path("arquivo-tecnico/", include("technical_repository.urls", namespace="technical_repository")),
    path("report_maker/", include("report_maker.urls", namespace="report_maker")),
]

if getattr(settings, "ENABLE_DEVTOOLS", False):
    urlpatterns += [
        path("__dev__/", include("devtools.urls", namespace="devtools")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
