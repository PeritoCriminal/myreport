
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls', namespace='home')),
    path("contas/", include("accounts.urls")),
    path('rede/', include('social_net.urls')),
    path("grupos/", include("groups.urls", namespace="groups")),
    path("arquivo-tecnico/", include("technical_repository.urls", namespace="technical_repository")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)