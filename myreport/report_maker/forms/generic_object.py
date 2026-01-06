from django import forms

from report_maker.models import GenericExamObject


class GenericExamObjectForm(forms.ModelForm):
    """
    Formulário para criação e edição de objeto de exame genérico.
    """

    class Meta:
        model = GenericExamObject
        fields = [
            "title",
            "description",
            "methodology",
            "examination",
            "results",
            "order",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "methodology": forms.Textarea(attrs={"rows": 4}),
            "examination": forms.Textarea(attrs={"rows": 4}),
            "results": forms.Textarea(attrs={"rows": 4}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }
