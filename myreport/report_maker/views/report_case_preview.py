# report_maker/views/report_case_preview.py
from __future__ import annotations

from django.http import Http404
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from report_maker.models import ReportCase
from report_maker.views.report_case import ReportCaseAuthorQuerySetMixin
from report_maker.views.report_outline import build_report_outline


class ReportCasePreviewView(
    LoginRequiredMixin,
    ReportCaseAuthorQuerySetMixin,
    DetailView,
):
    """
    Preview (HTML) do laudo em formato de “documento”.

    Finalidade:
    - Renderizar o laudo de forma contínua (sem botões/UX de editor), simulando o layout final.
    - Reusar a mesma “outline” utilizada no showpage/PDF para garantir consistência editorial.

    Controle de acesso:
    - usuário autenticado;
    - apenas o autor do laudo (ReportCaseAuthorQuerySetMixin).

    Observação:
    - Preview não altera dados; portanto não exige permissões de edição (can_edit_reports_effective).
    - Caso o usuário não seja autor, o queryset filtrado fará o DetailView responder 404.
    """
    model = ReportCase
    template_name = "report_maker/reportcase_preview.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None) -> ReportCase:
        """
        Mantém o comportamento padrão do DetailView com queryset filtrado.
        Se o objeto não existir (ou não pertencer ao autor), retorna 404.
        """
        obj = super().get_object(queryset=queryset)
        if not obj:
            raise Http404("Laudo não encontrado.")
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # O próprio report_detail já resolve objetos e blocos; aqui mantemos o preview
        # consistente com showpage/pdf.
        exam_objects_qs = (
            report.exam_objects.all()
            .prefetch_related("images")
            .order_by("order", "created_at")
        )

        text_blocks_qs = report.text_blocks.all().order_by("placement", "position", "created_at")

        # ✅ outline unificada (preview/showpage/pdf)
        outline, _n_top = build_report_outline(
            report=report,
            exam_objects_qs=exam_objects_qs,
            text_blocks_qs=text_blocks_qs,
            start_at=1,
            prepend_blocks=report.get_render_blocks(),
        )
        ctx["outline"] = outline

        return ctx
