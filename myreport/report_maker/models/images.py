import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Max


import os
from django.utils.text import get_valid_filename

def object_image_upload_path(instance, filename):
    obj = instance.content_object
    if not obj or not getattr(obj, "report_case_id", None):
        raise ValueError("ObjectImage precisa estar associado a um objeto com report_case.")

    # sanitiza nome do arquivo
    filename = get_valid_filename(os.path.basename(filename))

    return (
        f"reports/{obj.report_case_id}/"
        f"objects/{instance.content_type.model}/"
        f"{instance.object_id}/"
        f"{filename}"
    )


class ObjectImage(models.Model):
    """
    Imagem associada a um objeto de exame específico,
    com posição documental definida por índice.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de objeto",
    )
    object_id = models.UUIDField("Objeto")
    content_object = GenericForeignKey("content_type", "object_id")

    image = models.ImageField("Imagem", upload_to=object_image_upload_path, max_length=500)

    caption = models.CharField("Legenda", max_length=240, blank=True)

    index = models.PositiveIntegerField("Índice", default=0)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Imagem"
        verbose_name_plural = "Imagens"
        ordering = ["index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "index"],
                name="unique_image_index_per_object",
            )
        ]

    def save(self, *args, **kwargs):
        # auto-index (1..N) por objeto quando vier 0
        if not self.index:
            last_index = (
                self.__class__.objects.filter(
                    content_type=self.content_type,
                    object_id=self.object_id,
                )
                .aggregate(max_index=Max("index"))
                .get("max_index")
            )
            self.index = (last_index or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Figura {self.index}"
