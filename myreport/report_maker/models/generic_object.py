from django.db import models

from .exam_base import ExamObject
from report_maker.utils.renderable import (
    RenderableExamObjectMixin,
    ReportSection,
)


class GenericExamObject(RenderableExamObjectMixin, ExamObject):
    """
    Objeto de exame genérico.

    Utilizado quando o elemento periciado não se enquadra em uma tipificação
    específica (ex.: faca, arma de fogo, veículo, ferramenta etc.).

    Este modelo herda de ExamObject (base comum do laudo) e define explicitamente,
    por meio de whitelist, quais campos textuais são renderizáveis no laudo.

    Regras de renderização no laudo:
    - Cada instância corresponde a um Título 1.
    - Cada seção declarada em REPORT_SECTIONS corresponde a um Título 2.
    - Apenas seções com conteúdo significativo são exibidas.
    - Campos não listados em REPORT_SECTIONS jamais são renderizados,
      mesmo que possuam valor no banco de dados.
    """

    REPORT_SECTIONS = [
        ReportSection(
            key="description",
            title="Descrição",
            fmt="md",
            level=2,
        ),
        ReportSection(
            key="methodology",
            title="Metodologia",
            fmt="md",
            level=2,
        ),
        ReportSection(
            key="examination",
            title="Exame",
            fmt="md",
            level=2,
        ),
        ReportSection(
            key="results",
            title="Resultados",
            fmt="md",
            level=2,
        ),
    ]

    class Meta:
        verbose_name = "Objeto genérico"
        verbose_name_plural = "Objetos genéricos"

    def __str__(self) -> str:
        """
        Representação textual do objeto, priorizando o título informado
        pelo perito. Utiliza fallback seguro quando o título não estiver
        preenchido.
        """
        return self.title or f"Objeto genérico ({self.pk})"
