# report_maker/models/exam_base.py

from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Max
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse


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
        blank=True,
        null=True,  # <- importante para o "if self.order is None" funcionar
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
        "report_maker.ObjectImage",
        related_query_name="exam_object",
    )

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ("order",)
        constraints = [
            models.UniqueConstraint(
                fields=("report_case", "order"),
                name="uq_examobject_reportcase_order",
            )
        ]

    def save(self, *args, **kwargs):
        if self.order is None:
            last = (
                ExamObject.objects  # <- base: enxerga todos os filhos
                .filter(report_case=self.report_case)
                .aggregate(last_order=Max("order"))
                .get("last_order")
            )
            self.order = (last or 0) + 1

        super().save(*args, **kwargs)

    @property
    def concrete(self):
        """
        Retorna a instância concreta (filha) quando existir.
        Útil para preview/templates (downcast manual).
        """
        # mantenha esta lista enquanto você estiver com downcast manual
        for rel in ("publicroadexamobject", "genericexamobject"):
            if hasattr(self, rel):
                return getattr(self, rel)
        return self

    @property
    def concrete_model_name(self) -> str:
        """
        Nome do model concreto (ex.: 'genericexamobject', 'publicroadexamobject').
        Seguro para uso em template.
        """
        return self.concrete._meta.model_name

    @property
    def edit_url(self):
        c = self.concrete
        url_name = getattr(c, "edit_url_name", None)
        if not url_name:
            return None
        return reverse(url_name, args=[self.report_case_id, c.pk])

    @property
    def app_label(self) -> str:
        return self._meta.app_label

    @property
    def model_name(self) -> str:
        return self._meta.model_name

    @property
    def delete_url(self):
        c = self.concrete
        url_name = getattr(c, "delete_url_name", None)
        if not url_name:
            return None
        return reverse(url_name, args=[self.report_case_id, c.pk])

    def __str__(self) -> str:
        return self.title or f"Objeto ({self.pk})"
