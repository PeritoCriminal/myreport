# report_maker/views/exam_vehicle_inspection.py
from __future__ import annotations

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from common.mixins import BootstrapFormMixin, BootstrapFormViewMixin
from report_maker.forms.vehicle_inspection import VehicleInspectionExamObjectForm
from report_maker.models import ReportCase
from report_maker.models.exam_vehicle_inspection import VehicleInspectionExamObject
from report_maker.views.mixins import CanEditReportRequiredMixin, ReportCaseContextMixin, ReportCaseObjectGuardMixin


class VehicleInspectionExamObjectOwnedQuerySetMixin:
    """
    Garante que o objeto pertence ao usuário via report_case.author.

    Observação:
    - Mesmo com ReportCaseObjectGuardMixin (que garante pertencer ao report_pk da URL),
      este filtro adiciona uma “cerca” extra para impedir qualquer vazamento por pk
      e mantém a queryset consistente para Update/Delete.
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("report_case")
            .filter(report_case__author=self.request.user)
        )


class VehicleInspectionCreateView(
    CanEditReportRequiredMixin,
    ReportCaseContextMixin,
    BootstrapFormViewMixin,
    CreateView,
):
    """
    Cria uma Vistoria de Veículo (VehicleInspectionExamObject) vinculada a um ReportCase.

    Regras:
    - exige laudo editável (ReportCase.can_edit == True) via CanEditReportRequiredMixin;
    - report_case é determinado pelo parâmetro report_pk e injetado no contexto;
    - form recebe classes Bootstrap via BootstrapFormViewMixin.
    """
    model = VehicleInspectionExamObject
    form_class = VehicleInspectionExamObjectForm
    template_name = "report_maker/vehicle_inspection_form.html"

    # injeta classes Bootstrap no form
    form_base_class = BootstrapFormMixin
    mode = "create"

    def form_valid(self, form):
        """
        Amarra o objeto ao laudo da URL (não confia em payload).
        """
        self.get_report_case()
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class VehicleInspectionUpdateView(
    CanEditReportRequiredMixin,
    ReportCaseObjectGuardMixin,
    VehicleInspectionExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    BootstrapFormViewMixin,
    UpdateView,
):
    """
    Edita uma Vistoria de Veículo vinculada a um ReportCase.

    Proteções:
    - CanEditReportRequiredMixin bloqueia escrita se laudo estiver fechado;
    - ReportCaseObjectGuardMixin impede troca de pk “puxando” objeto de outro laudo;
    - Queryset filtrada por report_case__author para reforçar isolamento.
    """
    model = VehicleInspectionExamObject
    form_class = VehicleInspectionExamObjectForm
    template_name = "report_maker/vehicle_inspection_form.html"

    form_base_class = BootstrapFormMixin
    pk_url_kwarg = "pk"
    mode = "update"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class VehicleInspectionDeleteView(
    CanEditReportRequiredMixin,
    ReportCaseObjectGuardMixin,
    VehicleInspectionExamObjectOwnedQuerySetMixin,
    ReportCaseContextMixin,
    DeleteView,
):
    """
    Exclui uma Vistoria de Veículo vinculada a um ReportCase.

    Observação:
    - Template genérico de confirmação já usado por outros objetos.
    """
    model = VehicleInspectionExamObject
    template_name = "report_maker/object_confirm_delete.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
