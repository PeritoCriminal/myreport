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


def technical_document_upload_path(instance, filename):
    return (
        f"tech_archive/"
        f"{instance.document.created_by_id}/"
        f"{instance.document.topic.slug}/"
        f"{instance.document.id}/"
        f"v{instance.version}.pdf"
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

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


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
