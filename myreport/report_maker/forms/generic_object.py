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
            "order",
        )

        labels = {
            "title": "Título",
            "description": "Descrição",
            "methodology": "Metodologia",
            "examination": "Exame",
            "results": "Resultados",
            "order": "Ordem de exibição",
        }

        help_texts = {
            "title": "Identificação breve do objeto de exame.",
            "description": "Descrição geral do objeto examinado.",
            "methodology": "Procedimentos e técnicas empregados no exame.",
            "examination": "Descrição objetiva do exame realizado.",
            "results": "Resultados obtidos a partir do exame.",
            "order": "Define a posição do objeto na sequência do relatório.",
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
            "order": forms.NumberInput(
                attrs={
                    "min": 0,
                    "step": 1,
                }
            ),
        }
