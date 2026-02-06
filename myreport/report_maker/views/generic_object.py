# myreport/report_maker/views/generic_object.py
from __future__ import annotations

from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from accounts.mixins import CanEditReportsRequiredMixin

from report_maker.forms import GenericExamObjectForm
from report_maker.models import GenericExamObject
from report_maker.views.mixins import (
    CanEditReportRequiredMixin,
    ReportCaseContextMixin,
    ReportCaseObjectGuardMixin,
    ExamObjectImagesContextMixin,
)


class GenericExamObjectOwnedQuerySetMixin:
    """
    Garante que o objeto pertence ao usuário via report_case.author.
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("report_case")
            .filter(report_case__author=self.request.user)
        )


class GenericExamObjectCreateView(
    CanEditReportsRequiredMixin,  # ✅ nível usuário (validade/assinatura/vínculo)
    CanEditReportRequiredMixin,   # ✅ nível laudo (ReportCase.can_edit)
    ReportCaseContextMixin,
    CreateView,
):
    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"
    context_object_name = "obj"
    mode = "create"

    def form_valid(self, form):
        self.get_report_case()
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class GenericExamObjectUpdateView(
    CanEditReportsRequiredMixin,  # ✅ nível usuário
    CanEditReportRequiredMixin,   # ✅ nível laudo
    ReportCaseObjectGuardMixin,
    GenericExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,
    UpdateView,
):
    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"
    mode = "update"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class GenericExamObjectDeleteView(
    CanEditReportsRequiredMixin,  # ✅ nível usuário
    CanEditReportRequiredMixin,   # ✅ nível laudo
    ReportCaseObjectGuardMixin,
    GenericExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    DeleteView,
):
    model = GenericExamObject
    template_name = "report_maker/object_confirm_delete.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
