# social_net/forms.py
from django import forms
from .models import Post, PostComment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "text", "media"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Título",
            }),
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escreva algo...",
            }),
        }



# social_net/forms.py

class PostCommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ["text", "image"]
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Escreva um comentário...",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("text") or "").strip()
        image = cleaned.get("image")
        if not text and not image:
            raise forms.ValidationError("Informe texto ou imagem.")
        cleaned["text"] = text
        return cleaned
