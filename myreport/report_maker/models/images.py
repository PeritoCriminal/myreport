import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .report_case import ReportCase


def object_image_upload_path(instance, filename):
    """
    Define o caminho de upload das imagens vinculadas aos objetos de exame,
    organizadas por laudo, tipo de objeto e identificador do objeto.
    """
    return (
        f"reports/{instance.report_case_id}/"
        f"objects/{instance.content_type.model}/"
        f"{instance.object_id}/{filename}"
    )


class ObjectImage(models.Model):
    """
    Imagem associada a um objeto de exame específico,
    com posição documental definida por índice.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_case = models.ForeignKey(
        ReportCase,
        on_delete=models.CASCADE,
        related_name="object_images",
        verbose_name="Laudo",
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de objeto",
    )
    object_id = models.UUIDField("Objeto")
    content_object = GenericForeignKey("content_type", "object_id")

    image = models.ImageField("Imagem", upload_to=object_image_upload_path)
    caption = models.CharField("Legenda", max_length=240)
    index = models.PositiveIntegerField("Índice")

    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Imagem"
        verbose_name_plural = "Imagens"
        ordering = ["index"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "index"],
                name="unique_image_index_per_object",
            )
        ]

    def __str__(self):
        return f"Figura {self.index}"
