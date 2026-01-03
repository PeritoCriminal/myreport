import os
import uuid

from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator


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


def technical_document_upload_path(instance, filename: str) -> str:
    """
    Upload do PDF principal do documento.

    Estrutura:
    tech_archive/<created_by_id>/<topic_slug>/<document_id>/document.pdf
    """
    # Garante extensão .pdf (e evita nomes estranhos no storage)
    _, ext = os.path.splitext(filename)
    ext = (ext or ".pdf").lower()
    if ext != ".pdf":
        ext = ".pdf"

    return (
        f"tech_archive/"
        f"{instance.created_by_id}/"
        f"{instance.topic.slug}/"
        f"{instance.id}/"
        f"document{ext}"
    )


# TODO (futuro):
# Adicionar imagem de capa (cover) para o card do documento.
# - Field sugerido: cover_image = models.ImageField(...)
# - Armazenar em: tech_archive/<user>/<topic>/<doc_id>/cover.<ext>
# - (Opcional) gerar thumbnail leve (ex.: 800x450) ao salvar.


class TechnicalDocument(models.Model):
    """
    Documento técnico (um registro = um PDF)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    topic = models.ForeignKey(
        TechnicalTopic,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    pdf_file = models.FileField(
        upload_to=technical_document_upload_path,
        max_length=300,
        validators=[FileExtensionValidator(["pdf"])],
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="technical_documents",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title
