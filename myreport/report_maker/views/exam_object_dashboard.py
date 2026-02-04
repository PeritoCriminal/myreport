# report_maker/views/exam_object_dashboard.py
from __future__ import annotations

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from report_maker.models import ReportCase


class ExamObjectDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "report_maker/exam_object_dashboard.html"
    pk_url_kwarg = "pk"

    def get_report(self) -> ReportCase:
        report = get_object_or_404(ReportCase, pk=self.kwargs.get(self.pk_url_kwarg))
        if report.author_id != self.request.user.id:
            raise Http404("Laudo não encontrado.")
        return report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_report()
        context["report"] = report

        context["cards"] = [
            {
                "title": "Objeto genérico",
                "description": "Use para itens diversos do exame.",
                "icon": "bi-box",
                "url": reverse("report_maker:generic_object_create", kwargs={"report_pk": report.pk}),
                "enabled": report.can_edit,
            },
            {
                "title": "Exame de via pública",
                "description": "Condições climáticas, condições da via e sinalização viária.",
                "icon": "bi-signpost-2",
                "url": reverse("report_maker:public_road_object_create", kwargs={"report_pk": report.pk}),
                "enabled": report.can_edit,
            },
            {
                "title": "Vistoria de veículo",
                "description": "Descrição do veículo, metodologia aplicada, elementos observados e testes operacionais.",
                "icon": "bi-car-front",
                "url": reverse("report_maker:vehicle_inspection_create", kwargs={"report_pk": report.pk}),
                "enabled": report.can_edit,
            },
        ]
        return context
