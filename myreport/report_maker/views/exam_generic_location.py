# report_maker/views/exam_generic_location.py
from __future__ import annotations

from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from accounts.mixins import CanEditReportsRequiredMixin

from report_maker.forms import GenericLocationExamObjectForm
from report_maker.models import GenericLocationExamObject
from report_maker.views.mixins import (
    CanEditReportRequiredMixin,
    ReportCaseContextMixin,
    ReportCaseObjectGuardMixin,
    ExamObjectImagesContextMixin,
)


class GenericLocationExamObjectOwnedQuerySetMixin:
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


class GenericLocationExamObjectCreateView(
    CanEditReportsRequiredMixin,   # ✅ permissão de editar laudos (nível usuário)
    CanEditReportRequiredMixin,    # ✅ permissão de editar este laudo (nível ReportCase: can_edit)
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,  # opcional
    CreateView,
):
    model = GenericLocationExamObject
    form_class = GenericLocationExamObjectForm
    template_name = "report_maker/exam_generic_location_form.html"
    context_object_name = "obj"
    mode = "create"

    def form_valid(self, form):
        self.get_report_case()
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class GenericLocationExamObjectUpdateView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário
    CanEditReportRequiredMixin,    # ✅ nível ReportCase
    ReportCaseObjectGuardMixin,
    GenericLocationExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,
    UpdateView,
):
    model = GenericLocationExamObject
    form_class = GenericLocationExamObjectForm
    template_name = "report_maker/exam_generic_location_form.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"
    mode = "update"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class GenericLocationExamObjectDeleteView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário
    CanEditReportRequiredMixin,    # ✅ nível ReportCase
    ReportCaseObjectGuardMixin,
    GenericLocationExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    DeleteView,
):
    model = GenericLocationExamObject
    template_name = "report_maker/object_confirm_delete.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
