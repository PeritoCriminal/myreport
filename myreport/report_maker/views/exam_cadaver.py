# report_maker/views/exam_cadaver.py
from __future__ import annotations

from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from accounts.mixins import CanEditReportsRequiredMixin

from report_maker.forms import CadaverExamObjectForm
from report_maker.models import CadaverExamObject
from report_maker.views.mixins import (
    CanEditReportRequiredMixin,
    ReportCaseContextMixin,
    ReportCaseObjectGuardMixin,
    ExamObjectImagesContextMixin,
)


class CadaverExamObjectOwnedQuerySetMixin:
    """
    Garante que o usuário só manipule objetos vinculados a laudos de sua autoria.
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("report_case")
            .filter(report_case__author=self.request.user)
        )


class CadaverExamObjectCreateView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário (validade/assinatura/vínculo)
    CanEditReportRequiredMixin,    # ✅ nível laudo (ReportCase.can_edit)
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,  # opcional
    CreateView,
):
    model = CadaverExamObject
    form_class = CadaverExamObjectForm
    template_name = "report_maker/exam_cadaver_form.html"
    context_object_name = "obj"
    mode = "create"

    def form_valid(self, form):
        self.get_report_case()
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class CadaverExamObjectUpdateView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário
    CanEditReportRequiredMixin,    # ✅ nível laudo
    ReportCaseObjectGuardMixin,
    CadaverExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,
    UpdateView,
):
    model = CadaverExamObject
    form_class = CadaverExamObjectForm
    template_name = "report_maker/exam_cadaver_form.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"
    mode = "update"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class CadaverExamObjectDeleteView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário
    CanEditReportRequiredMixin,    # ✅ nível laudo
    ReportCaseObjectGuardMixin,
    CadaverExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    DeleteView,
):
    model = CadaverExamObject
    template_name = "report_maker/object_confirm_delete.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
