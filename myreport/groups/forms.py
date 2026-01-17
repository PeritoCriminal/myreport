# groups/forms.py

from django import forms

from common.mixins import BaseModelForm
from .models import Group


class GroupForm(BaseModelForm):
    class Meta:
        model = Group
        fields = [
            "name",
            "description",
            "profile_image",
            "background_image",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Nome do grupo",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Descrição do grupo",
                }
            ),
            "profile_image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
            "background_image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
        }
