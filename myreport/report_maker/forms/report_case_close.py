# report_maker/forms/report_case_close.py
from django import forms

from report_maker.models import ReportCase


class ReportCaseCloseForm(forms.ModelForm):
    """
    Minimal form to close a report by attaching the final PDF.

    Note:
    - The actual closing rules are enforced by ReportCase.close().
    """

    class Meta:
        model = ReportCase
        fields = ["pdf_file"]

    def save(self, commit=True):
        report: ReportCase = super().save(commit=False)

        # Close the report using the domain method (single source of truth)
        report.close(self.cleaned_data["pdf_file"])

        if commit:
            report.save()

        return report
