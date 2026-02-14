# path: myreport/report_maker/forms/object_image.py

from django import forms

from common.mixins import BaseModelForm
from report_maker.models import ObjectImage


class ObjectImageForm(BaseModelForm):
    """
    Formulário de upload de imagem vinculada a objeto de exame.
    A renderização do campo 'caption' é feita via text_block_editor no template.
    """
    TEXT_BLOCK_FIELDS = ("caption",)
    TEXT_BLOCK_ROWS = {"caption": 8}

    class Meta:
        model = ObjectImage
        fields = ["image", "caption"]
