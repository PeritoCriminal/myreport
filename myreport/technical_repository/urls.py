from django.urls import path

from .views import TechnicalDocumentListView, TechnicalDocumentCreateView

app_name = "technical_repository"

urlpatterns = [
    path("", TechnicalDocumentListView.as_view(), name="document_list"),
    path("novo/", TechnicalDocumentCreateView.as_view(), name="document_create"),
]
