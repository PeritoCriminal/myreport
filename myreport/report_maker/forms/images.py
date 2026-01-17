# report_maker/forms/object_image.py
from django import forms

from common.mixins import BaseModelForm
from report_maker.models import ObjectImage


class ObjectImageForm(BaseModelForm):
    """
    Formulário de upload de imagem vinculada a objeto de exame.
    """

    class Meta:
        model = ObjectImage
        fields = ["image", "caption"]
        widgets = {
            "caption": forms.Textarea(
                attrs={
                    "rows": 2,
                    "maxlength": 240,
                    "placeholder": "Legenda da imagem",
                }
            ),
        }
