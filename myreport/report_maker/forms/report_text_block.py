from django import forms

from report_maker.models.report_text_block import ReportTextBlock
from common.mixins import BootstrapFormMixin  


class ReportTextBlockForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ReportTextBlock
        fields = ["placement", "title", "body"]
        widgets = {
            "placement": forms.Select(),
            "title": forms.TextInput(attrs={
                "placeholder": "Opcional (ex.: Resumo, Considerações finais)"
            }),
            # body NÃO ganha widget aqui, pois é renderizado
            # pelo partial text_blockeditor.html
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return title.strip()
