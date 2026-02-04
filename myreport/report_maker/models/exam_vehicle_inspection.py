# report_maker/models/exam_vehicle_inspection.py

from __future__ import annotations

from django.db import models

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock
from .mixins import HasMethodologyMixin, HasObservedElementsMixin


class VehicleInspectionExamObject(HasMethodologyMixin, HasObservedElementsMixin, ExamObject):
    """
    Objeto de exame: Vistoria de Veículo.
    Foco: descrição do veículo, metodologia aplicada e constatações objetivas.
    """

    GROUP_KEY = ExamObjectGroup.VEHICLES

    edit_url_name = "report_maker:vehicle_inspection_update"
    delete_url_name = "report_maker:vehicle_inspection_delete"

    class MethodologyChoices(models.TextChoices):
        VISUAL_INSPECTION = "Vistoria Veicular", "Vistoria (inspeção visual)"
        LUMINOL = "Sangue Latente", "Luminol (pesquisa de sangue latente)"
        FORENSIC_LIGHTS = "FORENSIC_LIGHTS", "Busca por vestígios latentes com luzes forenses"

    methodology_kind = models.CharField(
        "Metodologia (tipo)",
        max_length=40,
        choices=MethodologyChoices.choices,
        blank=True,
        default="",
        help_text="Selecione o tipo principal de procedimento aplicado.",
    )

    operational_tests = models.TextField(
        "Testes operacionais",
        blank=True,
        help_text="Ex.: acionamentos, funcionamento de sistemas, verificações específicas.",
    )

    tire_conditions = models.TextField(
        "Condições dos pneus",
        blank=True,
        help_text="Ex.: estado geral, desgaste, calibragem (se aferida), avarias visíveis.",
    )

    optional_notes = models.TextField(
        "Texto opcional",
        blank=True,
        help_text="Campo livre para consignações técnicas pontuais relacionadas ao exame.",
    )

    class Meta:
        verbose_name = "Vistoria de Veículo"
        verbose_name_plural = "Vistorias de Veículos"
        ordering = ("order",)

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        """
        Seções abaixo do título do objeto.
        A view decide o nível absoluto de numeração.
        """
        return [
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {"kind": "section_field", "label": "Metodologia (tipo)", "field": "methodology_kind", "fmt": "text"},
            {"kind": "section_field", "label": "Metodologia", "field": "methodology", "fmt": "text"},
            {"kind": "section_field", "label": "Elementos observados", "field": "observed_elements", "fmt": "text"},
            {"kind": "section_field", "label": "Testes operacionais", "field": "operational_tests", "fmt": "text"},
            {"kind": "section_field", "label": "Condições dos pneus", "field": "tire_conditions", "fmt": "text"},
            {"kind": "section_field", "label": "Texto opcional", "field": "optional_notes", "fmt": "text"},
        ]

    def __str__(self) -> str:
        return self.title or f"Vistoria de Veículo ({self.pk})"
