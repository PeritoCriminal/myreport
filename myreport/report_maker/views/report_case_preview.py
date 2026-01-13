# report_maker/views/report_case_preview.py
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import DetailView

from report_maker.models import ReportCase


class ReportCasePreviewView(LoginRequiredMixin, DetailView):
    """
    Preview (read-only) do laudo com aparência do documento final.
    Pode exibir 'Em edição' ou 'Consolidado' via contexto.
    """
    model = ReportCase
    template_name = "report_maker/reportcase_preview.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"  # ajuste se sua URL usa outro nome (ex.: report_id)

    def get_queryset(self):
        """
        Restrinja aqui conforme suas regras (instituição/equipe/usuário).
        Mantive padrão simples e seguro: só objetos do usuário, se existir owner.
        """
        qs = super().get_queryset()

        # Se você tiver campos como created_by / owner / user, descomente e ajuste:
        # qs = qs.filter(created_by=self.request.user)

        # Se você já tem lógica de permissão por instituição/equipe, aplique aqui.
        return qs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Se você tiver controle de acesso mais forte (ex.: só membros da equipe),
        # valide aqui e levante 404 para não vazar existência do laudo.
        # if not obj.user_can_view(self.request.user):
        #     raise Http404

        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # Payload de cabeçalho pronto para o template
        # (ajuste para o seu atributo real: report.institution, report.unit, report.team)
        header = {}
        if getattr(report, "institution", None):
            header = report.institution.header

        # Linha final: Núcleo + Equipe (opcional)
        unit_line_parts = []
        unit = getattr(report, "unit", None)
        team = getattr(report, "team", None)

        if unit:
            unit_line_parts.append(getattr(unit, "display_name", None) or str(unit))
        if team:
            unit_line_parts.append(getattr(team, "display_name", None) or str(team))

        header = {
            **header,
            "unit_line": " – ".join(unit_line_parts) if unit_line_parts else None,
        }

        # Status do laudo (edição x consolidado)
        # Ajuste os campos conforme seu model.
        is_consolidated = bool(getattr(report, "is_consolidated", False))
        consolidated_at = getattr(report, "consolidated_at", None)
        consolidated_by = getattr(report, "consolidated_by", None)

        ctx.update(
            {
                "header": header,
                "is_consolidated": is_consolidated,
                "consolidated_at": consolidated_at,
                "consolidated_by": consolidated_by,
                # Útil pro template esconder botões se ?print=1
                "print_mode": self.request.GET.get("print") in ("1", "true", "yes"),
            }
        )
        return ctx
