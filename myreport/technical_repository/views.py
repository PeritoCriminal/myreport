from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.views import View

from .models import TechnicalDocument
from .forms import TechnicalDocumentForm


class TechnicalDocumentListView(LoginRequiredMixin, ListView):
    """
    Lista documentos técnicos ativos.

    Ordenação:
    1) Tema (ordem alfabética)
    2) Título do documento (ordem alfabética)
    """

    model = TechnicalDocument
    template_name = "technical_repository/document_list.html"
    context_object_name = "documents"
    paginate_by = 20

    def get_queryset(self):
        return (
            TechnicalDocument.objects
            .filter(is_active=True)
            .select_related("topic", "created_by")
            .order_by(
                "topic__name",
                "title",
            )
        )


class TechnicalDocumentCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de documento técnico (upload direto do PDF).
    """

    model = TechnicalDocument
    form_class = TechnicalDocumentForm
    template_name = "technical_repository/document_form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)   # ✔ define self.object
        self.object.created_by = self.request.user
        self.object.save()
        form.save_m2m()
        return super().form_valid(form)         # ✔ mantém o fluxo da CBV

    def get_success_url(self):
        return reverse(
            "technical_repository:document_detail",
            kwargs={"pk": self.object.pk},
        )




class TechnicalDocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe os detalhes do documento técnico.
    """

    model = TechnicalDocument
    template_name = "technical_repository/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return (
            TechnicalDocument.objects
            .filter(is_active=True)
            .select_related("topic", "created_by")
        )


class TechnicalDocumentUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView,
):
    """
    Edição do documento técnico.
    Permitida apenas ao criador do upload.
    """

    model = TechnicalDocument
    form_class = TechnicalDocumentForm
    template_name = "technical_repository/document_form.html"
    context_object_name = "document"

    def get_queryset(self):
        return TechnicalDocument.objects.filter(is_active=True)

    def test_func(self):
        return self.get_object().created_by == self.request.user

    def handle_no_permission(self):
        return redirect(
            "technical_repository:document_detail",
            pk=self.get_object().pk,
        )

    def get_success_url(self):
        return reverse(
            "technical_repository:document_detail",
            kwargs={"pk": self.object.pk},
        )







class TechnicalDocumentDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    View,
):
    """
    Deleção lógica do documento técnico.
    Apenas o criador pode excluir.
    """

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user

    def get_object(self):
        return get_object_or_404(
            TechnicalDocument,
            pk=self.kwargs["pk"],
            is_active=True,
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        return redirect(reverse("technical_repository:document_list"))
