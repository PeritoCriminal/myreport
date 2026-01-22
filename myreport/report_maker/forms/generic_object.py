# report_maker/forms/generic_exam_object.py
from django import forms

from common.mixins import BaseModelForm
from report_maker.models import GenericExamObject


class GenericExamObjectForm(BaseModelForm):
    """
    Formulário para criação e edição de objeto de exame genérico.
    """

    class Meta:
        model = GenericExamObject
        fields = (
            "title",
            "description",
        )

        labels = {
            "title": "Título",
            "description": "Descrição",
        }

        help_texts = {
            "title": "Identificação breve do objeto de exame.",
            "description": "Descrição geral do objeto examinado.",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "autocapitalize": "sentences",
                }
            ),
            "description": forms.Textarea(attrs={"rows": 4}),
        }
