# report_maker/models/exam_generic_location.py

from __future__ import annotations

from django.db import models

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock
from .mixins import HasObservedElementsMixin, HasServiceContextMixin
from report_maker.utils import GoogleMapsLocationMixin


class GenericLocationExamObject(
    GoogleMapsLocationMixin,
    HasServiceContextMixin,
    HasObservedElementsMixin,
    ExamObject,
):
    """
    Objeto de exame: Local genérico.

    Representa qualquer tipo de local de interesse pericial, mantendo identificação,
    descrição do local, referência de geolocalização (Google Maps), contexto do atendimento
    (preservação, presença da autoridade requisitante etc.) e elementos observados vinculados
    ao exame, para composição do laudo.
    """

    GROUP_KEY = ExamObjectGroup.LOCATIONS

    edit_url_name = "report_maker:generic_location_update"
    delete_url_name = "report_maker:generic_location_delete"

    geo_location = models.CharField(
        "Localização geográfica (Google Maps)",
        max_length=255,
        blank=True,
        null=True,
        help_text="Cole coordenadas, link do Maps, plus code ou endereço (uma linha).",
    )

    class Meta:
        verbose_name = "Local (genérico)"
        verbose_name_plural = "Locais (genéricos)"
        ordering = ("order",)

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        return [
            {"kind": "geo_location", "label": "Localização", "field": "geo_location"},
            {"kind": "section_field", "label": "Contexto do atendimento", "field": "service_context", "fmt": "text"},
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {"kind": "section_field", "label": "Google Maps", "field": "maps_url", "fmt": "text"},
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
            # não explode template/admin se usuário colar algo ruim
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
        return self.title or f"Local (genérico) ({self.pk})"
