# myreport/report_maker/models/exam_base.py

from __future__ import annotations

import uuid

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from .images import ObjectImage


class ExamObject(models.Model):
    """
    Base comum para todos os objetos examinados em um laudo.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    report_case = models.ForeignKey(
        "report_maker.ReportCase",
        on_delete=models.CASCADE,
        related_name="exam_objects",
        related_query_name="exam_object",
    )

    order = models.PositiveIntegerField(
        "Ordem",
        editable=False,
        blank=True,  # <- importante (form/admin)
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

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = False
        ordering = ("order",)
        constraints = [
            models.UniqueConstraint(
                fields=("report_case", "order"),
                name="uq_examobject_reportcase_order",
            )
        ]

    def save(self, *args, **kwargs):
        """
        Define automaticamente a ordem do objeto dentro do laudo.
        Ordem GLOBAL dentro do report_case.
        """
        if self.order is None:
            last = (
                ExamObject.objects
                .filter(report_case=self.report_case)
                .aggregate(models.Max("order"))
                .get("order__max")
            )
            self.order = (last or 0) + 1

        super().save(*args, **kwargs)


    @property
    def concrete(self):
        """
        Retorna a instância concreta (filha) quando existir.
        Útil para preview/templates (downcast manual).
        """
        for rel in ("publicroadexamobject", "genericexamobject"):
            if hasattr(self, rel):
                return getattr(self, rel)
        return self


@property
def concrete_model_name(self) -> str:
    """
    Nome do model concreto (ex.: 'genericexamobject', 'publicroadexamobject').
    Seguro para uso em template (não acessa _meta no template).
    """
    return self.concrete._meta.model_name

    def __str__(self) -> str:
        return self.title or f"Objeto ({self.pk})"
