from django import forms

from report_maker.models import ObjectImage
from common.form_mixins import BootstrapFormMixin


class ObjectImageForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulário de upload de imagem vinculada a objeto de exame.
    """

    class Meta:
        model = ObjectImage
        fields = ["image", "caption"]
        widgets = {
            "caption": forms.Textarea(attrs={
                "rows": 2,
                "maxlength": 240,
                "placeholder": "Legenda da imagem",
            }),
        }
