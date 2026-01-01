from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch
from django.views import View
from django.views.generic import ListView
from django.urls import reverse
from django.shortcuts import render, redirect


from .models import TechnicalDocument, TechnicalDocumentVersion
from .forms import TechnicalDocumentForm, TechnicalDocumentVersionCreateForm


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




class TechnicalDocumentCreateView(LoginRequiredMixin, View):
    template_name = "technical_repository/document_form.html"

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {
                "form": TechnicalDocumentForm(),
                "version_form": TechnicalDocumentVersionCreateForm(),
            },
        )

    def post(self, request, *args, **kwargs):
        form = TechnicalDocumentForm(request.POST, request.FILES)
        version_form = TechnicalDocumentVersionCreateForm(request.POST, request.FILES)

        if not (form.is_valid() and version_form.is_valid()):
            return render(
                request,
                self.template_name,
                {"form": form, "version_form": version_form},
            )

        with transaction.atomic():
            document = form.save(commit=False)
            document.created_by = request.user
            document.save()

            v1 = version_form.save(commit=False)
            v1.document = document
            v1.version = 1
            v1.is_current = True
            v1.created_by = request.user
            v1.save()

            TechnicalDocumentVersion.objects.filter(
                document=document
            ).exclude(pk=v1.pk).update(is_current=False)

        return redirect(reverse("technical_repository:document_list"))