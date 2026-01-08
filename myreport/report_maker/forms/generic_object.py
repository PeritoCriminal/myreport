from django import forms

from common.form_mixins import BootstrapFormMixin
from report_maker.models import GenericExamObject


class GenericExamObjectForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulário para criação e edição de objeto de exame genérico.
    """

    class Meta:
        model = GenericExamObject
        fields = (
            "title",
            "description",
            "methodology",
            "examination",
            "results",
        )

        labels = {
            "title": "Título",
            "description": "Descrição",
            "methodology": "Metodologia",
            "examination": "Exame",
            "results": "Resultados",
        }

        help_texts = {
            "title": "Identificação breve do objeto de exame.",
            "description": "Descrição geral do objeto examinado.",
            "methodology": "Procedimentos e técnicas empregados no exame.",
            "examination": "Descrição objetiva do exame realizado.",
            "results": "Resultados obtidos a partir do exame.",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "autocapitalize": "sentences",
                }
            ),
            "description": forms.Textarea(attrs={"rows": 4}),
            "methodology": forms.Textarea(attrs={"rows": 4}),
            "examination": forms.Textarea(attrs={"rows": 4}),
            "results": forms.Textarea(attrs={"rows": 4}),
        }
