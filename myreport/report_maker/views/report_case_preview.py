# report_maker/views/report_case_preview.py
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView

from report_maker.models import ReportCase, GenericExamObject  # + seu outro model aqui
from report_maker.utils.enumerator import TitleEnumerator


class ReportCasePreviewView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_preview.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # ⚠️ Ajuste/adicione os outros models que também são “objetos de exame”
        generic_qs = (
            GenericExamObject.objects
            .filter(report_case=report)
            .prefetch_related("images")
            .order_by("order", "pk")  # ajuste se seu campo for outro
        )

        # Exemplo: se você tem um model “Via Pública” separado, carregue aqui:
        # public_road_qs = (
        #     PublicRoadExamObject.objects
        #     .filter(report_case=report)
        #     .prefetch_related("images")
        #     .order_by("order", "pk")
        # )

        items = []

        for obj in generic_qs:
            items.append({
                "type": "GENERIC",
                "obj": obj,
                "detail_url": reverse("report_maker:generic_object_detail", args=[obj.pk]),
                "order": getattr(obj, "order", 0),
            })

        # for obj in public_road_qs:
        #     items.append({
        #         "type": "PUBLIC_ROAD",
        #         "obj": obj,
        #         "detail_url": reverse("report_maker:public_road_detail", args=[obj.pk]),
        #         "order": getattr(obj, "order", 0),
        #     })

        # Unifica e ordena (se ambos coexistem)
        items.sort(key=lambda x: (x.get("order", 0), x["obj"].pk))

        # Numeração pronta para o template
        enum = TitleEnumerator()
        for it in items:
            base = getattr(it["obj"], "title", "") or "Objeto sem título"
            it["display_title"] = enum.format(base)  # <-- ajuste se seu enumerator usar outro método

        ctx["exam_objects_ui"] = items
        return ctx
