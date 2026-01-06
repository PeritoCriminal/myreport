from django import forms

from report_maker.models import ReportCase


class ReportCaseForm(forms.ModelForm):
    """
    Formulário de criação e edição do Laudo.
    """

    class Meta:
        model = ReportCase
        fields = [
            "report_number",
            "protocol",
            "objective",
            "requesting_authority",
            "police_report",
            "police_inquiry",
            "police_station",
            "occurrence_datetime",
            "assignment_datetime",
            "examination_datetime",
            "photography_by",
            "sketch_by",
            "conclusion",
        ]
        widgets = {
            "occurrence_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "assignment_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "examination_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "conclusion": forms.Textarea(attrs={"rows": 6}),
        }
