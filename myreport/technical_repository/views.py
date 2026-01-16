# technical_repository/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views import View

from .models import TechnicalDocument
from .forms import TechnicalDocumentForm


class TechnicalDocumentListView(LoginRequiredMixin, ListView):
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


class TechnicalDocumentCreateView(LoginRequiredMixin, CreateView):
    model = TechnicalDocument
    form_class = TechnicalDocumentForm
    template_name = "technical_repository/document_form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        form.save_m2m()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("technical_repository:document_detail", kwargs={"pk": self.object.pk})


class TechnicalDocumentDetailView(LoginRequiredMixin, DetailView):
    model = TechnicalDocument
    template_name = "technical_repository/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return (
            TechnicalDocument.objects
            .filter(is_active=True)
            .select_related("topic", "created_by")
        )


class TechnicalDocumentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TechnicalDocument
    form_class = TechnicalDocumentForm
    template_name = "technical_repository/document_form.html"
    context_object_name = "document"

    raise_exception = True  # -> 403 (usa 403.html via handler403)

    def get_queryset(self):
        return TechnicalDocument.objects.filter(is_active=True)  # -> 404 (usa 404.html via handler404)

    def test_func(self):
        return self.get_object().created_by == self.request.user

    def get_success_url(self):
        return reverse("technical_repository:document_detail", kwargs={"pk": self.object.pk})


class TechnicalDocumentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True  # -> 403 (usa 403.html via handler403)

    def test_func(self):
        obj = self.get_object()
        return obj.created_by == self.request.user

    def get_object(self):
        return get_object_or_404(
            TechnicalDocument,
            pk=self.kwargs["pk"],
            is_active=True,  # -> 404 (usa 404.html via handler404)
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        return redirect(reverse("technical_repository:document_list"))
