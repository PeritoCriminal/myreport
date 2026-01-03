# technical_repository/urls.py

from django.urls import path

from .views import (
    TechnicalDocumentListView,
    TechnicalDocumentCreateView,
    TechnicalDocumentDetailView,
    TechnicalDocumentUpdateView,
    TechnicalDocumentDeleteView
)

app_name = "technical_repository"

urlpatterns = [
    # Lista do acervo técnico
    path(
        "",
        TechnicalDocumentListView.as_view(),
        name="document_list",
    ),

    # Criação (upload do PDF)
    path(
        "novo/",
        TechnicalDocumentCreateView.as_view(),
        name="document_create",
    ),

    # Detalhe do documento
    path(
        "<uuid:pk>/",
        TechnicalDocumentDetailView.as_view(),
        name="document_detail",
    ),

    # Edição (restrita ao criador)
    path(
        "<uuid:pk>/editar/",
        TechnicalDocumentUpdateView.as_view(),
        name="document_update",
    ),
    path(
        "<uuid:pk>/excluir/",
        TechnicalDocumentDeleteView.as_view(),
        name="document_delete",
    ),
]
