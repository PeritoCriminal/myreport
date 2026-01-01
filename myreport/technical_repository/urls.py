from django.urls import path

from .views import TechnicalDocumentListView

app_name = "technical_repository"

urlpatterns = [
    path("", TechnicalDocumentListView.as_view(), name="document_list"),
]
