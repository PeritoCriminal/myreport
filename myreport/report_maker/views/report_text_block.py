# report_maker/views/report_text_block.py

from __future__ import annotations

from django.http import Http404
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from report_maker.models import ReportCase
from report_maker.models.report_text_block import ReportTextBlock

from report_maker.forms import ReportTextBlockForm


# ─────────────────────────────────────────────────────────────
# Helpers / Mixins
# ─────────────────────────────────────────────────────────────

class ReportCaseContextMixin:
    """
    Carrega o ReportCase do URL e expõe no self.report_case.
    Garante que o laudo pertence ao usuário logado.
    """
    report_pk_url_kwarg = "report_pk"

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get(self.report_pk_url_kwarg)
        if not pk:
            raise Http404("ReportCase não informado.")

        try:
            self.report_case = (
                ReportCase.objects
                .select_related("author")
                .get(pk=pk, author=request.user)
            )
        except ReportCase.DoesNotExist:
            raise Http404("Laudo não encontrado.")

        # bloqueio lógico (não editar quando não pode)
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and not self.report_case.can_edit:
            raise Http404("Laudo bloqueado para edição.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report_case
        return ctx


# ─────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────

class ReportTextBlockListView(LoginRequiredMixin, ReportCaseContextMixin, ListView):
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_list.html"
    context_object_name = "blocks"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(report_case=self.report_case)
            .order_by("placement", "order", "created_at")
        )


class ReportTextBlockCreateView(LoginRequiredMixin, ReportCaseContextMixin, CreateView):
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_form.html"
    form_class = ReportTextBlockForm

    def get_initial(self):
        initial = super().get_initial()
        placement = self.request.GET.get("placement")
        if placement:
            initial["placement"] = placement
        return initial

    def form_valid(self, form):
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class ReportTextBlockUpdateView(LoginRequiredMixin, ReportCaseContextMixin, UpdateView):
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_form.html"
    form_class = ReportTextBlockForm
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return super().get_queryset().filter(report_case=self.report_case)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class ReportTextBlockDeleteView(LoginRequiredMixin, ReportCaseContextMixin, DeleteView):
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_confirm_delete.html"
    pk_url_kwarg = "pk"
    context_object_name = "block"

    def get_queryset(self):
        return super().get_queryset().filter(report_case=self.report_case)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
