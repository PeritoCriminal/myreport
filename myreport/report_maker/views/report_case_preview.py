# report_maker/views/report_case_preview.py
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.views.generic import DetailView

from report_maker.models import ReportCase
from report_maker.utils.enumerator import TitleEnumerator
from report_maker.utils.markdown_extras import render_markdown


class ReportCasePreviewView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_preview.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        exam_objects_qs = (
            self.model.exam_objects.rel.related_model.objects.all()
            .prefetch_related("images")
        )
        return (
            super()
            .get_queryset()
            .prefetch_related(Prefetch("exam_objects", queryset=exam_objects_qs))
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        ctx["header"] = report.header_context

        ctx["is_consolidated"] = (report.status == ReportCase.Status.CLOSED)
        ctx["consolidated_at"] = report.concluded_at
        ctx["consolidated_by"] = report.author
        ctx["print_mode"] = self.request.GET.get("print") in ("1", "true", "yes")

        enum = TitleEnumerator(strict=True)

        secno = {
            "dados_requisicao": enum.title(1),
            "dados_atendimento": enum.title(1),
        }
        if report.exam_objects.exists():
            secno["objetos_examinados"] = enum.title(1)

        enriched_objects = []
        for obj in report.exam_objects.all():
            obj.description_html = (
                render_markdown(obj.description) if getattr(obj, "description", "") else ""
            )
            obj.methodology_html = (
                render_markdown(obj.methodology) if getattr(obj, "methodology", "") else ""
            )
            obj.examination_html = (
                render_markdown(obj.examination) if getattr(obj, "examination", "") else ""
            )
            obj.results_html = (
                render_markdown(obj.results) if getattr(obj, "results", "") else ""
            )

            obj_no = enum.title(2)

            subnums = {}
            if obj.description_html:
                subnums["descricao"] = enum.title(3)
            if obj.methodology_html:
                subnums["metodologia"] = enum.title(3)
            if obj.examination_html:
                subnums["exame"] = enum.title(3)
            if obj.results_html:
                subnums["resultados"] = enum.title(3)

            images = list(obj.images.all()) if hasattr(obj, "images") else []
            for img in images:
                img.figure_label = enum.figure()
                caption = getattr(img, "caption", "") or ""
                img.caption_html = render_markdown(caption) if caption else ""

            obj.preview_images = images

            enriched_objects.append(
                {
                    "obj": obj,
                    "obj_no": obj_no,
                    "subnums": subnums,
                    "images": images,
                }
            )

        ctx["secno"] = secno
        ctx["enriched_objects"] = enriched_objects

        return ctx
