from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView

from common.mixins import BootstrapFormViewMixin, BootstrapFormMixin, CanEditReportsRequiredMixin
from report_maker.forms.vehicle_inspection import VehicleInspectionExamObjectForm
from report_maker.models import ReportCase
from report_maker.models.exam_vehicle_inspection import VehicleInspectionExamObject


class ReportCaseContextMixin:
    """
    Mantém a view autocontida e injeta `report` no contexto.
    """

    report: ReportCase

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(ReportCase, pk=kwargs["report_pk"])

        # regra mínima (ajuste se tiver permissão mais sofisticada por laudo)
        if self.report.author_id != request.user.id:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report
        return ctx

"""
class VehicleInspectionListView(CanEditReportsRequiredMixin, ReportCaseContextMixin, ListView):
    model = VehicleInspectionExamObject
    template_name = "report_maker/vehicle_inspection/object_list.html"
    context_object_name = "objects"

    def get_queryset(self):
        return VehicleInspectionExamObject.objects.filter(report_case=self.report).order_by("order")


class VehicleInspectionDetailView(CanEditReportsRequiredMixin, ReportCaseContextMixin, DetailView):
    model = VehicleInspectionExamObject
    template_name = "report_maker/vehicle_inspection/object_detail.html"
    context_object_name = "object"

    def get_queryset(self):
        return VehicleInspectionExamObject.objects.filter(report_case=self.report)
"""

class VehicleInspectionCreateView(
    CanEditReportsRequiredMixin,
    ReportCaseContextMixin,
    BootstrapFormViewMixin,
    CreateView,
):
    model = VehicleInspectionExamObject
    form_class = VehicleInspectionExamObjectForm
    template_name = "report_maker/vehicle_inspection_form.html"

    # injeta classes Bootstrap no form
    form_base_class = BootstrapFormMixin

    def form_valid(self, form):
        form.instance.report_case = self.report
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", args=[self.report.pk])


class VehicleInspectionUpdateView(
    CanEditReportsRequiredMixin,
    ReportCaseContextMixin,
    BootstrapFormViewMixin,
    UpdateView,
):
    model = VehicleInspectionExamObject
    form_class = VehicleInspectionExamObjectForm
    template_name = "report_maker/vehicle_inspection_form.html"

    form_base_class = BootstrapFormMixin

    def get_queryset(self):
        return VehicleInspectionExamObject.objects.filter(report_case=self.report)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", args=[self.report.pk])


class VehicleInspectionDeleteView(LoginRequiredMixin, CanEditReportsRequiredMixin, ReportCaseContextMixin, DeleteView):
    model = VehicleInspectionExamObject
    template_name = "report_maker/object_confirm_delete.html"
    context_object_name = "object"

    def get_queryset(self):
        return VehicleInspectionExamObject.objects.filter(report_case=self.report)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", args=[self.report.pk])
