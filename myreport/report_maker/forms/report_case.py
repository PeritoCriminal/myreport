# report_maker/forms/report_case.py
from __future__ import annotations

from django import forms

from common.mixins import BaseModelForm
from report_maker.models import ReportCase

DT_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class ReportCaseForm(BaseModelForm):
    """
    Formulário de criação e edição do Laudo.

    - DateTimeInput com type="datetime-local"
    - Classe JS para padronização automática de campos de protocolo
    - Validação de coerência temporal
    """

    DATETIME_LOCAL_INPUT_FORMATS = (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    )

    def _dt_widget(self) -> forms.DateTimeInput:
        return forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_LOCAL_FORMAT)

    # sobrescreve os campos para controlar widget + input_formats
    occurrence_datetime = forms.DateTimeField(
        required=False,
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_LOCAL_FORMAT),
        label="Ocorrência",
    )
    assignment_datetime = forms.DateTimeField(
        required=False,
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_LOCAL_FORMAT),
        label="Designação",
    )
    examination_datetime = forms.DateTimeField(
        required=False,
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_LOCAL_FORMAT),
        label="Exame pericial",
    )

    class Meta:
        model = ReportCase
        fields = [
            "report_number",
            "protocol",
            "objective",
            "institution",
            "nucleus",
            "team",
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
        ]
        # não repete widgets aqui porque já foram definidos nos campos acima
        widgets = {}

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
        # Render correto do datetime-local no EDIT
        # ─────────────────────────────────────
        for field_name in ("occurrence_datetime", "assignment_datetime", "examination_datetime"):
            if field_name in self.fields:
                value = self.initial.get(field_name) or getattr(self.instance, field_name, None)
                if value:
                    self.initial[field_name] = value.strftime(DT_LOCAL_FORMAT)

    def clean(self):
        cleaned = super().clean()

        occurrence = cleaned.get("occurrence_datetime")
        assignment = cleaned.get("assignment_datetime")
        examination = cleaned.get("examination_datetime")

        if occurrence and examination and examination < occurrence:
            raise forms.ValidationError(
                "A data do exame pericial não pode ser anterior à data da ocorrência."
            )

        if assignment and examination and examination < assignment:
            raise forms.ValidationError(
                "A data do exame pericial não pode ser anterior à data da designação."
            )

        return cleaned
