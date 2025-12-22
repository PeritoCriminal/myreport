# social_net/forms.py
import os
from django import forms
from .models import Post, PostComment


class PostForm(forms.ModelForm):
    # Ajuste aqui, se quiser
    ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".m4v"}
    MAX_VIDEO_SIZE_MB = 200  # limite simples (MB)

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
           "media": forms.ClearableFileInput(attrs={"accept": "image/*,video/*"}),
        }

    def clean_media(self):
        f = self.cleaned_data.get("media")
        if not f:
            return f

        ext = os.path.splitext(getattr(f, "name", ""))[1].lower()

        IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
        VIDEO_EXTS = self.ALLOWED_VIDEO_EXTS

        if ext in IMAGE_EXTS:
            # imagem: aceita (otimização já ocorre depois)
            return f

        if ext in VIDEO_EXTS:
            size = getattr(f, "size", 0) or 0
            max_bytes = self.MAX_VIDEO_SIZE_MB * 1024 * 1024
            if size > max_bytes:
                raise forms.ValidationError(
                    f"Vídeo muito grande ({size / (1024 * 1024):.1f} MB). "
                    f"Máximo: {self.MAX_VIDEO_SIZE_MB} MB."
                )
            return f

        allowed = ", ".join(sorted(IMAGE_EXTS | VIDEO_EXTS))
        raise forms.ValidationError(
            f"Formato de mídia não permitido. Use: {allowed}."
        )



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
