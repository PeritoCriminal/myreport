from __future__ import annotations

from django import forms

from common.mixins import BootstrapFormMixin
from report_maker.models.report_text_block import ReportTextBlock


class ReportTextBlockForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulário de criação/edição de blocos de texto do laudo.

    `group_key` é determinado pelo sistema. Para textos de grupo
    (OBJECT_GROUP_INTRO), a view deve injetar `instance.group_key`.
    """

    class Meta:
        model = ReportTextBlock
        fields = ["placement", "body"]
        widgets = {
            "placement": forms.Select(),
        }

    def clean_body(self) -> str:
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError("O texto do laudo não pode ficar em branco.")
        return body

    def clean(self):
        cleaned = super().clean()
        placement = cleaned.get("placement")

        report_case = getattr(self.instance, "report_case", None)
        if not report_case or not placement:
            return cleaned

        if placement in ReportTextBlock.SINGLETON_PLACEMENTS:
            qs = ReportTextBlock.objects.filter(
                report_case=report_case,
                placement=placement,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error("placement", "Este tipo de texto já existe neste laudo.")

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            group_key = (getattr(self.instance, "group_key", "") or "").strip()
            if not group_key or group_key == ReportTextBlock.GLOBAL_GROUP_KEY:
                self.add_error(
                    "placement",
                    "Grupo do texto não informado para este tipo de bloco."
                )

        return cleaned
