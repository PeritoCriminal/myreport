from django import forms

from report_maker.models import ObjectImage
from common.form_mixins import BootstrapFormMixin


class ObjectImageForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulário de upload de imagem vinculada a objeto de exame.
    """

    class Meta:
        model = ObjectImage
        fields = [
            "image",
            "caption",
            "index",
        ]
        widgets = {
            "caption": forms.TextInput(attrs={"maxlength": 240}),
            "index": forms.NumberInput(attrs={"min": 1}),
        }
