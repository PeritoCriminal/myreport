# myreport/report_maker/models/exam_base.py

from __future__ import annotations

import uuid
from django.db import models

from .report_case import ReportCase


class ExamObject(models.Model):
    """
    Base comum para todos os objetos examinados em um laudo.

    Define apenas os campos conceituais mínimos compartilhados por todos os
    tipos de objeto pericial, independentemente de sua natureza específica
    (local, veículo, arma, cadáver, etc.).

    Campos narrativos adicionais devem ser introduzidos por mixins ou
    modelos concretos, conforme a necessidade de cada tipo.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    report_case = models.ForeignKey(
        ReportCase,
        on_delete=models.CASCADE,
        related_name="exam_objects",
        verbose_name="Laudo",
    )

    title = models.CharField(
        "Título do objeto",
        max_length=160,
        blank=True,
        help_text="Identificação sucinta do objeto no laudo.",
    )

    description = models.TextField(
        "Descrição",
        blank=True,
        help_text="Descrição geral e identificadora do objeto examinado.",
    )

    created_at = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.title or f"Objeto ({self.pk})"
