# myreport/report_maker/models/exam_base.py

from __future__ import annotations

import uuid

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from .report_case import ReportCase
from .images import ObjectImage


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

    order = models.PositiveIntegerField(
        "Ordem",
        editable=False,
        help_text="Ordem de exibição do objeto dentro do laudo.",
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

    images = GenericRelation(
        ObjectImage,
        related_query_name="exam_object",
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
        ordering = ("order",)

    def save(self, *args, **kwargs):
        """
        Define automaticamente a ordem do objeto dentro do laudo,
        caso ainda não tenha sido atribuída.
        """
        if self.order is None:
            last = (
                self.__class__.objects
                .filter(report_case=self.report_case)
                .aggregate(models.Max("order"))
                .get("order__max")
            )
            self.order = (last or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title or f"Objeto ({self.pk})"
