# report_maker/models/exam_public_road.py

from __future__ import annotations

from django.db import models

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock
from .mixins import HasObservedElementsMixin, HasServiceContextMixin
from report_maker.utils import GoogleMapsLocationMixin


class PublicRoadExamObject(
    GoogleMapsLocationMixin,
    HasServiceContextMixin,
    HasObservedElementsMixin,
    ExamObject,
):
    """
    Objeto de exame: Via Pública.
    """

    GROUP_KEY = ExamObjectGroup.LOCATIONS

    edit_url_name = "report_maker:public_road_object_update"
    delete_url_name = "report_maker:public_road_object_delete"

    geo_location = models.CharField(
        "Localização geográfica (Google Maps)",
        max_length=255,
        blank=True,
        null=True,
        help_text="Cole coordenadas, link do Maps, plus code ou endereço (uma linha).",
    )

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
            {"kind": "geo_location", "label": "Localização", "field": "geo_location"},
            {"kind": "section_field", "label": "Contexto do atendimento", "field": "service_context", "fmt": "text"},
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {"kind": "section_field", "label": "Sinalização viária", "field": "traffic_signage", "fmt": "text"},
            {"kind": "section_field", "label": "Condições da via", "field": "road_conditions", "fmt": "text"},
            {"kind": "section_field", "label": "Condições climáticas", "field": "weather_conditions", "fmt": "text"},
            {"kind": "section_field", "label": "Elementos observados", "field": "observed_elements", "fmt": "text"},
        ]

    @property
    def geo_data(self) -> dict | None:
        """
        Retorna dict com:
          - maps_url
          - lat/lng (quando extraível)
          - raw_query
          - qrcode_png (bytes PNG)
        ou None se não informado / inválido.
        """
        value = (self.geo_location or "").strip()
        if not value:
            return None

        try:
            return self.parse_location_line(value)
        except Exception:
            return None

    @property
    def geo_maps_url(self) -> str | None:
        d = self.geo_data
        return d.get("maps_url") if d else None

    @property
    def geo_qrcode_png(self) -> bytes | None:
        d = self.geo_data
        return d.get("qrcode_png") if d else None

    def __str__(self) -> str:
        return self.title or f"Exame de Via Pública ({self.pk})"
