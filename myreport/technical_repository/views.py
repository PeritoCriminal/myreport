# technical_repository/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views import View

from common.mixins import ProfileImageContextMixin
from .models import TechnicalDocument
from .forms import TechnicalDocumentForm


class TechnicalDocumentListView(
    LoginRequiredMixin,
    ProfileImageContextMixin,
    ListView,
):
    model = TechnicalDocument
    template_name = "technical_repository/document_list.html"
    context_object_name = "documents"
    paginate_by = 20

    def get_queryset(self):
        return (
            TechnicalDocument.objects
            .filter(is_active=True)
            .select_related("topic", "created_by")
            .order_by("topic__name", "title")
        )


class TechnicalDocumentCreateView(
    LoginRequiredMixin,
    ProfileImageContextMixin,
    CreateView,
):
    model = TechnicalDocument
    form_class = TechnicalDocumentForm
    template_name = "technical_repository/document_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("technical_repository:document_list")


class TechnicalDocumentDetailView(
    LoginRequiredMixin,
    ProfileImageContextMixin,
    DetailView,
):
    model = TechnicalDocument
    template_name = "technical_repository/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        # inativo -> 404 (e usa seu template 404.html)
        return TechnicalDocument.objects.filter(is_active=True)


class TechnicalDocumentUpdateView(
    UserPassesTestMixin,          # <- vem ANTES do LoginRequiredMixin
    LoginRequiredMixin,
    ProfileImageContextMixin,
    UpdateView,
):
    raise_exception = True         # <- anônimo -> 403 (não redirect)
    model = TechnicalDocument
    form_class = TechnicalDocumentForm
    template_name = "technical_repository/document_form.html"

    def get_queryset(self):
        # inativo -> 404
        return TechnicalDocument.objects.filter(is_active=True)

    def test_func(self):
        return self.get_object().created_by == self.request.user

    def get_success_url(self):
        return reverse(
            "technical_repository:document_detail",
            kwargs={"pk": self.object.pk},
        )


class TechnicalDocumentDeleteView(UserPassesTestMixin, LoginRequiredMixin, ProfileImageContextMixin, View):
    raise_exception = True

    def get_queryset(self):
        return TechnicalDocument.objects.filter(is_active=True)

    def test_func(self):
        # pega o objeto "cru" (ativo ou inativo) só para checar dono
        obj = get_object_or_404(TechnicalDocument, pk=self.kwargs["pk"])
        return obj.created_by_id == self.request.user.id

    def post(self, request, pk):
        obj = get_object_or_404(self.get_queryset(), pk=pk)  # aqui inativo vira 404
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        return redirect("technical_repository:document_list")
