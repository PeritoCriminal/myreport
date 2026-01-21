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
        """
        Prefetch para evitar N+1 e garantir que objetos/imagens venham prontos para o preview.
        """
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

        # Cabeçalho do laudo (OPEN: via FKs / CLOSED: via snapshots)
        ctx["header"] = report.header_context

        # Flags úteis
        ctx["is_consolidated"] = (report.status == ReportCase.Status.CLOSED)
        ctx["consolidated_at"] = report.concluded_at
        ctx["consolidated_by"] = report.author
        ctx["print_mode"] = self.request.GET.get("print") in ("1", "true", "yes")

        # Markdown + Numeração (preview HTML) — sem templatetags
        enum = TitleEnumerator()

        # Prepara HTML para cada objeto e CACHEIA imagens já enriquecidas
        # (atributos anexados em runtime; não persistem no banco)
        for obj in report.exam_objects.all():
            obj.description_html = render_markdown(obj.description) if getattr(obj, "description", "") else ""
            obj.methodology_html = render_markdown(obj.methodology) if getattr(obj, "methodology", "") else ""
            obj.examination_html = render_markdown(obj.examination) if getattr(obj, "examination", "") else ""
            obj.results_html = render_markdown(obj.results) if getattr(obj, "results", "") else ""

            # Imagens: legenda markdown + fallback "Figura N"
            images = list(obj.images.all()) if hasattr(obj, "images") else []
            for img in images:
                img.figure_label = enum.figure()  # "Figura 1", "Figura 2", ...
                caption = getattr(img, "caption", "") or ""
                img.caption_html = render_markdown(caption) if caption else ""

            # IMPORTANTE: o template deve iterar obj.preview_images (não obj.images.all)
            obj.preview_images = images

        return ctx
