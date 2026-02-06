# report_maker/forms/report_case_close.py
from common.mixins import BaseModelForm
from report_maker.models import ReportCase


class ReportCaseCloseForm(BaseModelForm):
    """
    Form mínimo para concluir um laudo (sem anexar PDF arquivado).

    Nota:
    - As regras de fechamento são aplicadas por ReportCase.close().
    """

    class Meta:
        model = ReportCase
        fields: list[str] = []  # sem campos (apenas confirmação/submit)

    def save(self, commit: bool = True) -> ReportCase:
        report: ReportCase = super().save(commit=False)

        # Fecha o laudo usando o método de domínio (fonte única de verdade)
        report.close()

        if commit:
            report.save()

        return report
