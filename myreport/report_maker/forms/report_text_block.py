from django import forms

from report_maker.models.report_text_block import ReportTextBlock
from common.mixins import BootstrapFormMixin  


class ReportTextBlockForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ReportTextBlock
        fields = ["placement", "group_key", "title", "body"]
        widgets = {
            "placement": forms.Select(),
            "group_key": forms.TextInput(attrs={
                "placeholder": "Ex.: LOCATIONS, VEHICLES, CADAVER",
            }),
            "title": forms.TextInput(attrs={
                "placeholder": "Opcional (título padrão será usado)"
            }),
            # body continua sendo renderizado no editor
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return title.strip()

    def clean_group_key(self):
        group_key = (self.cleaned_data.get("group_key") or "").strip()
        return group_key

    def clean(self):
        cleaned = super().clean()
        placement = cleaned.get("placement")
        group_key = (cleaned.get("group_key") or "").strip()

        # se o report_case ainda não estiver injetado (GET/POST inicial),
        # não estoura erro aqui; a view garante depois
        report_case = getattr(self.instance, "report_case", None)
        if not report_case:
            return cleaned

        # group_key obrigatório só para texto de grupo
        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            if not group_key:
                self.add_error(
                    "group_key",
                    "Informe o tipo de objeto (ex.: LOCATIONS, VEHICLES)."
                )
            else:
                cleaned["group_key"] = group_key
        else:
            cleaned["group_key"] = ""

        # evita duplicação amigável para placements únicos
        if placement in ReportTextBlock.SINGLETON_PLACEMENTS:
            qs = ReportTextBlock.objects.filter(
                report_case=report_case,
                placement=placement,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    "placement",
                    "Este tipo de texto já existe neste laudo."
                )

        return cleaned


        # evita duplicação amigavelmente (antes do DB)
        if placement in ReportTextBlock.SINGLETON_PLACEMENTS:
            qs = ReportTextBlock.objects.filter(
                report_case=self.instance.report_case,
                placement=placement,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    "placement",
                    "Este tipo de texto já existe neste laudo."
                )

        return cleaned
