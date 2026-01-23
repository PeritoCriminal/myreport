from __future__ import annotations

from django.db import models

from .exam_base import ExamObject
from .mixins import HasObservedElementsMixin


class PublicRoadExamObject(HasObservedElementsMixin, ExamObject):
    """
    Objeto de exame: Via Pública.
    """

    weather_conditions = models.TextField(
        "Condições climáticas",
        blank=True,
    )

    road_conditions = models.TextField(
        "Condições da via",
        blank=True,
    )

    traffic_signage = models.TextField(
        "Sinalização viária",
        blank=True,
    )

    class Meta:
        verbose_name = "Exame de Via Pública"
        verbose_name_plural = "Exames de Via Pública"
