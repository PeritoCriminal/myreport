# myreport/report_maker/models/exam_public_road.py

from __future__ import annotations

from django.db import models

from .exam_base import ExamObject
from .mixins import HasObservedElementsMixin


class PublicRoadExamObject(HasObservedElementsMixin, ExamObject):
    """
    Objeto de exame: Via Pública.
    """

    # nomes das rotas (usados pelo ExamObject para resolver reverse)
    edit_url_name = "report_maker:public_road_object_update"
    delete_url_name = "report_maker:public_road_object_delete"

    weather_conditions = models.TextField("Condições climáticas", blank=True)
    road_conditions = models.TextField("Condições da via", blank=True)
    traffic_signage = models.TextField("Sinalização viária", blank=True)

    class Meta:
        verbose_name = "Exame de Via Pública"
        verbose_name_plural = "Exames de Via Pública"
        ordering = ("order",)

    def __str__(self) -> str:
        return self.title or f"Exame de Via Pública ({self.pk})"
