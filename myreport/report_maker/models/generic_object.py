# myreport/report_maker/models/generic_object.py

from django.db import models

from .exam_base import ExamObject
from report_maker.utils.renderable import RenderableExamObjectMixin, ReportSection


class GenericExamObject(RenderableExamObjectMixin, ExamObject):
    """
    Objeto de exame genérico.
    """

    RENDER_SECTIONS = [
        ReportSection(key="exam", title="Exame", fmt="md", level=2),
        ReportSection(key="results", title="Resultados", fmt="md", level=2),
    ]

    class Meta:
        verbose_name = "Objeto genérico"
        verbose_name_plural = "Objetos genéricos"
        ordering = ("order",)

    def __str__(self) -> str:
        return self.title or f"Objeto genérico ({self.pk})"
