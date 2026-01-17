# technical_repository/forms.py

from django import forms
from django.core.exceptions import ValidationError

from common.mixins import BaseModelForm
from .models import TechnicalDocument


class TechnicalDocumentForm(BaseModelForm):
    class Meta:
        model = TechnicalDocument
        fields = ["title", "description", "topic", "pdf_file"]

        widgets = {
            "title": forms.TextInput(),
            "description": forms.Textarea(attrs={"rows": 4}),
            "topic": forms.Select(),
            "pdf_file": forms.ClearableFileInput(),
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
