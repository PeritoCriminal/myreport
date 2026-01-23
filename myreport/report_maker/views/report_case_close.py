# report_maker/views/report_case_close.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import UpdateView

from report_maker.models import ReportCase
from report_maker.forms.report_case_close import ReportCaseCloseForm


class ReportCaseCloseView(LoginRequiredMixin, UpdateView):
    """
    View responsável pela CONCLUSÃO do laudo pericial.

    Responsabilidades:
    - permitir o upload do PDF final;
    - acionar o método de domínio `ReportCase.close()` (via form.save());
    - congelar organização (snapshot);
    - impedir conclusão duplicada.
    """

    model = ReportCase
    form_class = ReportCaseCloseForm
    template_name = "report_maker/reportcase_close.html"
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None):
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
        report = form.save()

        messages.success(
            self.request,
            "Laudo concluído e congelado com sucesso."
        )

        return redirect(
            reverse("report_maker:reportcase_detail", kwargs={"pk": report.pk})
        )
