# report_maker/views/report_case_close.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
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
    - acionar o método de domínio `ReportCase.close()`;
    - congelar a organização (Institution / Nucleus / Team);
    - impedir reabertura ou conclusão duplicada.

    Importante:
    Esta view NÃO altera campos isoladamente.
    Toda a regra de negócio está centralizada no model.
    """

    model = ReportCase
    form_class = ReportCaseCloseForm
    template_name = "report_maker/reportcase_close.html"

    # ------------------------------------------------------------------
    # Request gatekeeper
    # ------------------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        """
        Ponto de entrada da view (GET ou POST).

        Atua como "porteiro":
        - se o laudo já estiver concluído ou bloqueado,
          o acesso à tela de conclusão é negado;
        - evita dupla finalização e erros tardios.
        """
        report = self.get_object()

        if not report.can_edit:
            messages.warning(
                request,
                "Este laudo já foi concluído e não pode ser alterado."
            )
            return redirect(
                reverse("report_maker:report_detail", kwargs={"pk": report.pk})
            )

        return super().dispatch(request, *args, **kwargs)

    # ------------------------------------------------------------------
    # Object retrieval
    # ------------------------------------------------------------------
    def get_object(self, queryset=None):
        """
        Recupera o laudo a ser concluído a partir do UUID informado na URL.
        """
        return get_object_or_404(ReportCase, pk=self.kwargs["pk"])

    # ------------------------------------------------------------------
    # Successful form handling
    # ------------------------------------------------------------------
    def form_valid(self, form):
        """
        Finaliza o laudo com base no PDF enviado.

        Efeitos colaterais controlados:
        - status → CLOSED
        - bloqueio de edição
        - congelamento do snapshot organizacional
        - registro do horário de conclusão
        """
        report = form.save()

        messages.success(
            self.request,
            "Laudo concluído e congelado com sucesso."
        )

        return redirect(
            reverse("report_maker:report_detail", kwargs={"pk": report.pk})
        )
