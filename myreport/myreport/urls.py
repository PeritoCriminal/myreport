# myreport/urls.py

"""
URLConf do projeto.

Define o roteamento principal da aplicação, delegando os caminhos aos apps
responsáveis e mantendo rotas condicionais de desenvolvimento quando habilitadas.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("report_maker/", include("report_maker.urls", namespace="report_maker")),
    path("arquivo-tecnico/", include("technical_repository.urls", namespace="technical_repository")),
    path("grupos/", include("groups.urls", namespace="groups")),
    path("rede/", include("social_net.urls")),
    path("accounts/", include("accounts.urls")),
    path("", include("home.urls", namespace="home")),
]

if getattr(settings, "ENABLE_DEVTOOLS", False):
    urlpatterns += [
        path("__dev__/", include("devtools.urls", namespace="devtools")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)