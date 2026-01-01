import uuid
import os
from io import BytesIO

from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile

# Pillow
from PIL import Image


class TechnicalTopic(models.Model):
    """
    Tema técnico do acervo (ex.: Medicina Legal, Balística, etc.)
    """
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


def technical_document_upload_path(instance, filename):
    return (
        f"tech_archive/"
        f"{instance.document.created_by_id}/"
        f"{instance.document.topic.slug}/"
        f"{instance.document.id}/"
        f"v{instance.version}.pdf"
    )


def technical_cover_upload_path(instance, filename):
    # guarda numa pasta do documento
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    return (
        f"tech_archive/"
        f"{instance.created_by_id}/"
        f"{instance.topic.slug}/"
        f"{instance.id}/"
        f"cover{ext}"
    )


class TechnicalDocument(models.Model):
    """
    Documento lógico (agrupa versões)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    topic = models.ForeignKey(
        TechnicalTopic,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="technical_documents",
    )

    # ===== NOVO: imagem de topo do card =====
    cover_image = models.ImageField(
        upload_to=technical_cover_upload_path,
        blank=True,
        null=True,
        # essa imagem default deve estar em MEDIA (veja nota abaixo)
        default="tech_archive/defaults/pdf_img.png",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Reduz a imagem automaticamente (mantendo proporção) para uso em card.
        - Converte para JPEG (pra ficar leve), exceto se tiver alpha e você quiser manter PNG.
        - Tamanho sugerido: 640x360 (16:9) ou 800x450.
        """
        super().save(*args, **kwargs)

        if not self.cover_image:
            return

        try:
            img_path = self.cover_image.path
        except Exception:
            # storage remoto sem path
            return

        # evita reprocessar a imagem default (opcional)
        if self.cover_image.name.endswith("defaults/pdf_img.png"):
            return

        MAX_W, MAX_H = 800, 450  # ajuste: topo de card "wide"
        QUALITY = 82

        try:
            with Image.open(img_path) as im:
                im = im.convert("RGB")  # garante JPEG sem alpha
                im.thumbnail((MAX_W, MAX_H), Image.Resampling.LANCZOS)

                buffer = BytesIO()
                im.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
                buffer.seek(0)

            # grava como cover.jpg (substitui o original)
            new_name = os.path.splitext(self.cover_image.name)[0] + ".jpg"
            self.cover_image.save(new_name, ContentFile(buffer.read()), save=False)

            super().save(update_fields=["cover_image"])
        except Exception:
            # em caso de erro, não derruba o save do objeto
            return


class TechnicalDocumentVersion(models.Model):
    """
    Versões do PDF (imutáveis)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document = models.ForeignKey(
        TechnicalDocument,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version = models.PositiveIntegerField()
    pdf_file = models.FileField(
        upload_to=technical_document_upload_path,
        max_length=300,
        validators=[FileExtensionValidator(["pdf"])],
    )

    notes = models.TextField(blank=True)

    is_current = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="technical_document_versions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        unique_together = ("document", "version")

    def save(self, *args, **kwargs):
        if self.is_current:
            TechnicalDocumentVersion.objects.filter(
                document=self.document,
                is_current=True,
            ).update(is_current=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document.title} — v{self.version}"
