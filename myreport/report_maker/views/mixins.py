# myreport/report_maker/views/mixins.py
from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.http import Http404
from report_maker.models import ReportCase


class ReportCaseOwnedMixin:
    """
    Carrega o ReportCase e garante que pertence ao usuário autenticado.
    Faz cache em self.report_case para evitar múltiplas queries quando vários mixins chamam get_report_case().
    """
    report_pk_url_kwarg = "report_pk"

    def get_report_case(self) -> ReportCase:
        if hasattr(self, "report_case") and self.report_case is not None:
            return self.report_case

        pk = self.kwargs.get(self.report_pk_url_kwarg)
        if not pk:
            raise Http404("ReportCase não informado.")

        try:
            report = ReportCase.objects.select_related("author").get(pk=pk)
        except ReportCase.DoesNotExist:
            raise Http404("ReportCase não encontrado.")

        if report.author_id != self.request.user.id:
            raise PermissionDenied("Você não tem permissão para acessar este laudo.")

        self.report_case = report
        return report


class CanEditReportRequiredMixin(ReportCaseOwnedMixin):
    """
    Bloqueia qualquer operação de escrita quando report_case.can_edit == False.
    """
    def dispatch(self, request, *args, **kwargs):
        self.get_report_case()
        if not getattr(self.report_case, "can_edit", False):
            raise PermissionDenied("Este laudo não pode ser editado no momento.")
        return super().dispatch(request, *args, **kwargs)


class ReportCaseContextMixin(ReportCaseOwnedMixin):
    """
    Padroniza o context:
    - report -> self.report_case
    - obj -> self.object (quando existir) ou None (create)
    - mode -> "create" | "update" (se útil no template)
    """
    mode: str | None = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.get_report_case()
        ctx["report"] = self.report_case

        # padrão "obj" em create/update
        ctx.setdefault("obj", getattr(self, "object", None))

        if self.mode:
            ctx["mode"] = self.mode
        return ctx


class ReportCaseObjectGuardMixin(ReportCaseOwnedMixin):
    """
    Garante que o objeto consultado pertence ao report_case da URL.
    Útil para impedir trocar pk e "puxar" objeto de outro laudo do mesmo autor.
    """
    report_case_field_name = "report_case"  # FK no model

    def get_object(self, queryset=None):
        self.get_report_case()
        obj = super().get_object(queryset=queryset)

        fk = getattr(obj, f"{self.report_case_field_name}_id", None)
        if fk != self.report_case.id:
            raise Http404("Objeto não pertence a este laudo.")
        return obj
