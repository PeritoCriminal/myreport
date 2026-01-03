# technical_repository/forms.py

from django import forms
from django.core.exceptions import ValidationError

from .models import TechnicalDocument, TechnicalDocumentVersion


class TechnicalDocumentForm(forms.ModelForm):
    class Meta:
        model = TechnicalDocument
        fields = ["title", "description", "topic"]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "topic": forms.Select(attrs={"class": "form-select"}),
        }


class TechnicalDocumentVersionCreateForm(forms.ModelForm):
    """
    Form exclusivo para criação da versão inicial (v1).
    O usuário não escolhe "version" nem "is_current".
    """

    class Meta:
        model = TechnicalDocumentVersion
        fields = ["pdf_file", "notes"]

        widgets = {
            "pdf_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def clean_pdf_file(self):
        f = self.cleaned_data.get("pdf_file")

        if not f:
            raise ValidationError("Selecione um arquivo PDF.")

        name = (getattr(f, "name", "") or "").lower()
        if not name.endswith(".pdf"):
            raise ValidationError("O arquivo deve estar no formato PDF.")

        max_mb = 25
        if getattr(f, "size", 0) > max_mb * 1024 * 1024:
            raise ValidationError(f"O arquivo excedeu o limite de {max_mb} MB.")

        return f
