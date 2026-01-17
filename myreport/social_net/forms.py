# social_net/forms.py
import os

from django import forms

from common.mixins import BaseModelForm
from groups.models import Group, GroupMembership

from .models import Post, PostComment


class PostForm(BaseModelForm):
    ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".m4v"}
    MAX_VIDEO_SIZE_MB = 200  # limite simples (MB)

    group = forms.ModelChoiceField(
        label="Destino",
        required=False,
        queryset=Group.objects.none(),
        empty_label="Público",
    )

    class Meta:
        model = Post
        fields = ["group", "title", "text", "media"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Título"}),
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Escreva algo..."}),
            "media": forms.ClearableFileInput(attrs={"accept": "image/*,video/*"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # guarda referência se você quiser usar depois em clean_*
        self.user = user

        if user and getattr(user, "is_authenticated", False):
            self.fields["group"].queryset = Group.objects.filter(
                id__in=GroupMembership.objects.filter(user_id=user.pk).values("group_id")
            ).order_by("name")

        # garante group como select (form-select)
        if "group" in self.fields:
            classes = (self.fields["group"].widget.attrs.get("class") or "").split()
            classes = [c for c in classes if c != "form-control"]
            if "form-select" not in classes:
                classes.append("form-select")
            self.fields["group"].widget.attrs["class"] = " ".join(classes)

    def clean_group(self):
        return self.cleaned_data.get("group")

    def clean_media(self):
        f = self.cleaned_data.get("media")
        if not f:
            return f

        ext = os.path.splitext(getattr(f, "name", ""))[1].lower()

        IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
        VIDEO_EXTS = self.ALLOWED_VIDEO_EXTS

        if ext in IMAGE_EXTS:
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
        raise forms.ValidationError(f"Formato de mídia não permitido. Use: {allowed}.")


class PostCommentForm(BaseModelForm):
    class Meta:
        model = PostComment
        fields = ["text", "image"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Escreva um comentário...",
                }
            ),
        }

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("text") or "").strip()
        image = cleaned.get("image")
        if not text and not image:
            raise forms.ValidationError("Informe texto ou imagem.")
        cleaned["text"] = text
        return cleaned
