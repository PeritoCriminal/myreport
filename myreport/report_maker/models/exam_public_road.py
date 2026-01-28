# report_maker/models/exam_public_road.py

from __future__ import annotations

from django.db import models

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock
from .mixins import HasObservedElementsMixin


class PublicRoadExamObject(HasObservedElementsMixin, ExamObject):
    """
    Objeto de exame: Via Pública.
    """

    GROUP_KEY = ExamObjectGroup.LOCATIONS

    edit_url_name = "report_maker:public_road_object_update"
    delete_url_name = "report_maker:public_road_object_delete"

    weather_conditions = models.TextField("Condições climáticas", blank=True)
    road_conditions = models.TextField("Condições da via", blank=True)
    traffic_signage = models.TextField("Sinalização viária", blank=True)

    class Meta:
        verbose_name = "Exame de Via Pública"
        verbose_name_plural = "Exames de Via Pública"
        ordering = ("order",)

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        """
        Aqui ficam as SEÇÕES (títulos abaixo do title do objeto).
        A view decide o nível absoluto.
        """
        return [
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {"kind": "section_field", "label": "Sinalização viária", "field": "traffic_signage", "fmt": "text"},
            {"kind": "section_field", "label": "Condições da via", "field": "road_conditions", "fmt": "text"},
            {"kind": "section_field", "label": "Condições climáticas", "field": "weather_conditions", "fmt": "text"},
            {"kind": "section_field", "label": "Elementos observados", "field": "observed_elements", "fmt": "text"},
        ]

    def __str__(self) -> str:
        return self.title or f"Exame de Via Pública ({self.pk})"
