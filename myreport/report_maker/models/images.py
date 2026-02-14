# report_maker/models/object_image.py

import os
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Max
from django.utils.text import get_valid_filename


def object_image_upload_path(instance: "ObjectImage", filename: str) -> str:
    """
    Caminho:
      reports/<report_case_id>/objects/<app_label>/<model>/<object_id>/<filename>

    Observação:
      - exige que o content_object possua report_case_id (padrão ExamObject).
    """
    obj = instance.content_object
    if not obj or not getattr(obj, "report_case_id", None):
        raise ValueError("ObjectImage precisa estar associado a um objeto com report_case.")

    filename = get_valid_filename(os.path.basename(filename))

    return (
        f"reports/{obj.report_case_id}/"
        f"objects/{instance.content_type.app_label}/{instance.content_type.model}/"
        f"{instance.object_id}/"
        f"{filename}"
    )


class ObjectImage(models.Model):
    """
    Imagem associada a um objeto (via GenericForeignKey),
    com posição documental definida por índice (Figura 1..N) por objeto.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de objeto",
    )
    object_id = models.UUIDField("Objeto")
    content_object = GenericForeignKey("content_type", "object_id")

    image = models.ImageField(
        "Imagem",
        upload_to=object_image_upload_path,
        max_length=500,
    )

    caption = models.CharField("Legenda", max_length=240, blank=True)

    # Índice (Figura 1..N) por objeto.
    # Mantido como nullable para permitir "não informado" e auto-index na criação.
    index = models.PositiveIntegerField("Índice", null=True, blank=True)

    # dimensões originais da imagem (base para todas as transformações)
    original_width = models.PositiveIntegerField(
        "Largura original (px)",
        help_text="Largura da imagem original em pixels.",
    )
    original_height = models.PositiveIntegerField(
        "Altura original (px)",
        help_text="Altura da imagem original em pixels.",
    )

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
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def clean(self):
        super().clean()
        if self.index is not None and self.index <= 0:
            raise ValidationError({"index": "O índice deve ser um inteiro positivo (>= 1)."})

    def _calc_next_index(self) -> int:
        last_index = (
            self.__class__.objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
            )
            .aggregate(max_index=Max("index"))
            .get("max_index")
        )
        return (last_index or 0) + 1
    

    @property
    def width_cm_dot(self):
        # Usamos float para garantir que a divisão funcione
        # e forçamos a conversão para string com ponto
        if self.original_width:
            calculo = float(self.original_width) / 114.2857
            return "{:.2f}".format(calculo)
        return "14.00"
        

    def save(self, *args, **kwargs):
        """
        Auto-index:
          - apenas na criação (self._state.adding)
          - apenas quando index não for informado
        Proteção simples contra corrida:
          - tenta salvar
          - se colidir UniqueConstraint, recalcula e tenta de novo (poucas tentativas)
        """
        # valida coerência básica
        if self.object_id and not isinstance(self.object_id, uuid.UUID):
            raise ValueError("object_id deve ser UUID.")

        if self._state.adding and not self.index:
            # poucas tentativas resolvem a maior parte dos casos concorrentes
            for _ in range(3):
                self.index = self._calc_next_index()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    # provável colisão de índice; tenta recalcular
                    self.index = None
            # se ainda colidir, propaga para o caller tratar
            raise

        return super().save(*args, **kwargs)

    def __str__(self):
        # quando index ainda não foi atribuído (ex.: antes de salvar)
        return f"Figura {self.index or '-'}"
