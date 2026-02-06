# report_maker/views/report_case_close.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import UpdateView

from accounts.mixins import CanEditReportsRequiredMixin
from report_maker.forms.report_case_close import ReportCaseCloseForm
from report_maker.models import ReportCase


class ReportCaseCloseView(
    LoginRequiredMixin,
    CanEditReportsRequiredMixin,
    UpdateView,
):
    """
    View responsável pela CONCLUSÃO do laudo pericial.

    Conceito atual:
    - concluir o laudo significa CONGELAR seu estado lógico;
    - após a conclusão, o laudo não pode mais ser editado;
    - o PDF é um ARTEFATO DERIVADO e pode ser gerado a qualquer momento,
      não sendo mais exigido no fluxo de conclusão.

    Responsabilidades:
    - validar acesso do autor;
    - impedir conclusão duplicada;
    - acionar a regra de domínio `ReportCase.close()` (via form.save());
    - preservar snapshots institucionais associados ao laudo.
    """

    model = ReportCase
    form_class = ReportCaseCloseForm
    template_name = "report_maker/reportcase_close.html"
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None) -> ReportCase:
        report = get_object_or_404(ReportCase, pk=self.kwargs[self.pk_url_kwarg])

        # acesso restrito ao autor
        if report.author_id != self.request.user.id:
            raise Http404("Laudo não encontrado.")

        return report

    def dispatch(self, request, *args, **kwargs):
        report = self.get_object()

        # se já estiver fechado/bloqueado, não entra na tela
        if not report.can_edit:
            messages.warning(
                request,
                "Este laudo já foi concluído e não pode ser alterado."
            )
            return redirect(
                reverse("report_maker:reportcase_detail", kwargs={"pk": report.pk})
            )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        report: ReportCase = form.save()

        messages.success(
            self.request,
            "Laudo concluído e congelado com sucesso."
        )

        return redirect(
            reverse("report_maker:reportcase_detail", kwargs={"pk": report.pk})
        )
