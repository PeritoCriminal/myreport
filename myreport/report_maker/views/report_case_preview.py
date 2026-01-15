# report_maker/views/report_case_preview.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from report_maker.models import ReportCase


class ReportCasePreviewView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_preview.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # Cabeçalho agora vem do próprio laudo:
        # - OPEN: via FKs
        # - CLOSED: via snapshots (congelado)
        ctx["header"] = report.header_context
        print(f'\n----------------\n{report.header_context}\n----------------')

        # Flags úteis (se você quiser exibir badge/estado no template)
        ctx["is_consolidated"] = (report.status == ReportCase.Status.CLOSED)
        ctx["consolidated_at"] = report.concluded_at
        ctx["consolidated_by"] = report.author

        ctx["print_mode"] = self.request.GET.get("print") in ("1", "true", "yes")
        return ctx
