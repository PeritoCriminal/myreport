# myreport/report_maker/models/exam_base.py

import uuid
from django.db import models
from django.db.models import Max
from django.contrib.contenttypes.fields import GenericRelation

from .report_case import ReportCase


class ExamObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_case = models.ForeignKey(
        ReportCase,
        on_delete=models.CASCADE,
        related_name="exam_objects",
        verbose_name="Laudo",
    )

    title = models.CharField("Título", max_length=160, blank=True)

    description = models.TextField("Descrição", blank=True)
    methodology = models.TextField("Metodologia", blank=True)
    examination = models.TextField("Exame", blank=True)
    results = models.TextField("Resultados", blank=True)

    order = models.PositiveIntegerField("Ordem", default=0)

    # ✅ Relação reversa: cada objeto terá suas imagens
    images = GenericRelation(
        "report_maker.ObjectImage",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="exam_object",
    )

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        if not self.order:
            last_order = (
                self.__class__.objects
                .filter(report_case=self.report_case)
                .aggregate(max_order=Max("order"))
                .get("max_order")
            )
            self.order = (last_order or 0) + 1

        super().save(*args, **kwargs)
