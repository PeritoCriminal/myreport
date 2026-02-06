# myreport/report_maker/views/exam_public_road.py
from __future__ import annotations

from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from accounts.mixins import CanEditReportsRequiredMixin

from report_maker.forms import PublicRoadExamObjectForm
from report_maker.models import PublicRoadExamObject
from report_maker.views.mixins import (
    CanEditReportRequiredMixin,
    ReportCaseContextMixin,
    ReportCaseObjectGuardMixin,
    ExamObjectImagesContextMixin,
)


class PublicRoadExamObjectOwnedQuerySetMixin:
    """
    Garante que o objeto pertence ao usuário via report_case.author.
    (cinto e suspensório: o guard já garante pertencer ao report_pk)
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("report_case")
            .filter(report_case__author=self.request.user)
        )


class PublicRoadExamObjectCreateView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário (validade/assinatura/vínculo)
    CanEditReportRequiredMixin,    # ✅ nível laudo (ReportCase.can_edit)
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,  # opcional
    CreateView,
):
    model = PublicRoadExamObject
    form_class = PublicRoadExamObjectForm
    template_name = "report_maker/public_road_form.html"
    context_object_name = "obj"
    mode = "create"

    def form_valid(self, form):
        self.get_report_case()
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class PublicRoadExamObjectUpdateView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário
    CanEditReportRequiredMixin,    # ✅ nível laudo
    ReportCaseObjectGuardMixin,
    PublicRoadExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    ExamObjectImagesContextMixin,
    UpdateView,
):
    model = PublicRoadExamObject
    form_class = PublicRoadExamObjectForm
    template_name = "report_maker/public_road_form.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"
    mode = "update"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class PublicRoadExamObjectDeleteView(
    CanEditReportsRequiredMixin,   # ✅ nível usuário
    CanEditReportRequiredMixin,    # ✅ nível laudo
    ReportCaseObjectGuardMixin,
    PublicRoadExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    DeleteView,
):
    model = PublicRoadExamObject
    template_name = "report_maker/object_confirm_delete.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
