# report_maker/models/generic_object.py

from django.db import models

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock
from report_maker.utils.renderable import RenderableExamObjectMixin, ReportSection


class GenericExamObject(RenderableExamObjectMixin, ExamObject):
    """
    Objeto de exame genérico.
    """

    GROUP_KEY = ExamObjectGroup.OTHER

    edit_url_name = "report_maker:generic_object_update"
    delete_url_name = "report_maker:generic_object_delete"

    # Mantido como está no seu projeto
    RENDER_SECTIONS = [
        ReportSection(key="exam", title="Exame", fmt="md", level=2),
        ReportSection(key="results", title="Resultados", fmt="md", level=2),
    ]

    class Meta:
        verbose_name = "Objeto genérico"
        verbose_name_plural = "Objetos genéricos"
        ordering = ("order",)

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        """
        Para o genérico, você já tem seções renderizáveis (md) via mixin.
        Então expomos essas seções como blocos (título abaixo do title do objeto).
        """
        return [
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {"kind": "render_section", "label": "Exame", "key": "exam", "fmt": "md"},
            {"kind": "render_section", "label": "Resultados", "key": "results", "fmt": "md"},
        ]

    def __str__(self) -> str:
        return self.title or f"Objeto genérico ({self.pk})"
