from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.views.generic import ListView

from .models import (
    TechnicalDocument,
    TechnicalDocumentVersion,
)


class TechnicalDocumentListView(LoginRequiredMixin, ListView):
    """
    Lista documentos técnicos existentes.

    Ordenação:
    1) Tema (ordem alfabética)
    2) Título do documento (ordem alfabética)

    Exibe apenas documentos ativos e
    pré-carrega a versão atual.
    """

    model = TechnicalDocument
    template_name = "technical_repository/document_list.html"
    context_object_name = "documents"
    paginate_by = 20

    def get_queryset(self):
        current_versions = TechnicalDocumentVersion.objects.filter(
            is_current=True
        )

        qs = (
            TechnicalDocument.objects
            .filter(is_active=True)
            .select_related("topic", "created_by")
            .prefetch_related(
                Prefetch(
                    "versions",
                    queryset=current_versions,
                    to_attr="current_versions",
                )
            )
            .order_by(
                "topic__name",   # classificação
                "title",         # alfabética
            )
        )

        return qs
