# report_maker/models/exam_public_road.py

from __future__ import annotations

from django.db import models

from report_maker.utils import GoogleMapsLocationMixin

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock
from .mixins import HasObservedElementsMixin, HasServiceContextMixin


class PublicRoadExamObject(
    GoogleMapsLocationMixin,
    HasServiceContextMixin,
    HasObservedElementsMixin,
    ExamObject,
):
    """
    Objeto de exame destinado à descrição e ao registro de elementos técnicos de via pública.

    O objeto agrega campos específicos (localização, sinalização, condições da via e climáticas),
    além dos campos e comportamentos providos por `ExamObject` e pelos mixins de contexto do
    atendimento e elementos observados.

    Quando o campo `title` não é informado, aplica-se automaticamente o valor de `DEFAULT_TITLE`.
    """

    DEFAULT_TITLE = "Descrição e Exame do Local"

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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.title:
            self.title = self.DEFAULT_TITLE

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        """
        Define a sequência de blocos renderizáveis do objeto no relatório.

        A hierarquia/nível absoluto de títulos é responsabilidade da camada de view/template;
        este método declara apenas a ordem e o mapeamento entre rótulos e campos.
        """
        return [
            {"kind": "geo_location", "label": "Localização", "field": "geo_location"},
            {
                "kind": "section_field",
                "label": "Contexto do atendimento",
                "field": "service_context",
                "fmt": "text",
            },
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {
                "kind": "section_field",
                "label": "Sinalização viária",
                "field": "traffic_signage",
                "fmt": "text",
            },
            {
                "kind": "section_field",
                "label": "Condições da via",
                "field": "road_conditions",
                "fmt": "text",
            },
            {
                "kind": "section_field",
                "label": "Condições climáticas",
                "field": "weather_conditions",
                "fmt": "text",
            },
            {
                "kind": "section_field",
                "label": "Elementos observados",
                "field": "observed_elements",
                "fmt": "text",
            },
        ]

    @property
    def geo_data(self) -> dict | None:
        """
        Normaliza e interpreta `geo_location`, quando informado.

        Retorna um dicionário com dados derivados, conforme `GoogleMapsLocationMixin`, incluindo:
        - maps_url
        - lat / lng (quando extraíveis)
        - raw_query
        - qrcode_png (bytes PNG)

        Retorna `None` quando `geo_location` estiver vazio ou não puder ser interpretado.
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
        """
        Retorna a URL do Google Maps derivada de `geo_location`, quando disponível.
        """
        data = self.geo_data
        return data.get("maps_url") if data else None

    @property
    def geo_qrcode_png(self) -> bytes | None:
        """
        Retorna o QR Code (PNG em bytes) derivado de `geo_location`, quando disponível.
        """
        data = self.geo_data
        return data.get("qrcode_png") if data else None

    def __str__(self) -> str:
        """
        Representação textual do objeto para uso administrativo e depuração.
        """
        return self.title or f"Exame de Via Pública ({self.pk})"
        