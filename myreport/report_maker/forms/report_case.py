from django import forms

from common.form_mixins import BootstrapFormMixin
from report_maker.models import ReportCase

DT_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"

class ReportCaseForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulário de criação e edição do Laudo.

    Ajustes principais:
    - Padronizou DateTimeInput com type="datetime-local" + formatos compatíveis.
    - Aplicou classe JS para padronização automática de campos de protocolo.
    - Centralizou validação de coerência temporal.
    """

    DATETIME_LOCAL_INPUT_FORMATS = (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    )

    occurrence_datetime = forms.DateTimeField(
        required=False,
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Ocorrência",
    )
    assignment_datetime = forms.DateTimeField(
        required=False,
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Designação",
    )
    examination_datetime = forms.DateTimeField(
        required=False,
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Exame pericial",
    )

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
            "criminal_typification",
            "occurrence_datetime",
            "assignment_datetime",
            "examination_datetime",
            "photography_by",
            "sketch_by",
            "conclusion",
        ]
        widgets = {
            "conclusion": forms.Textarea(
                attrs={"rows": 6}),
            "occurrence_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format=DT_LOCAL_FORMAT,
            ),
            "assignment_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format=DT_LOCAL_FORMAT,
            ),
            "examination_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format=DT_LOCAL_FORMAT,
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ─────────────────────────────────────
        # Classe JS para ajuste de protocolo
        # ─────────────────────────────────────
        protocol_class = "js-adjust-protocol"

        for field_name in ("report_number", "protocol", "police_report", "police_inquiry"):
            if field_name in self.fields:
                attrs = self.fields[field_name].widget.attrs
                css_class = attrs.get("class", "")
                attrs["class"] = f"{css_class} {protocol_class}".strip()

        # ─────────────────────────────────────
        # Correção de renderização datetime-local (EDIT)
        # ─────────────────────────────────────
        DT_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"

        for field_name in (
            "occurrence_datetime",
            "assignment_datetime",
            "examination_datetime",
        ):
            if field_name in self.fields:
                value = self.initial.get(field_name) or getattr(self.instance, field_name, None)
                if value:
                    self.initial[field_name] = value.strftime(DT_LOCAL_FORMAT)


    def clean(self):
        cleaned_data = super().clean()

        occurrence = cleaned_data.get("occurrence_datetime")
        assignment = cleaned_data.get("assignment_datetime")
        examination = cleaned_data.get("examination_datetime")

        if occurrence and examination and examination < occurrence:
            raise forms.ValidationError(
                "A data do exame pericial não pode ser anterior à data da ocorrência."
            )

        if assignment and examination and examination < assignment:
            raise forms.ValidationError(
                "A data do exame pericial não pode ser anterior à data da designação."
            )

        return cleaned_data
