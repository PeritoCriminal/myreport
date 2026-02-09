# path: myreport/report_maker/models/report_text_block.py

from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Max, Q

from .report_case import ReportCase


class ReportTextBlock(models.Model):
    """
    Representa um bloco estrutural de texto do laudo pericial.

    Cada bloco é identificado por um tipo (placement) e por uma chave de grupo
    (group_key). O título exibido no laudo não é persistido, sendo derivado
    dessas informações.
    """

    GLOBAL_GROUP_KEY = "__GLOBAL__"

    class Placement(models.TextChoices):
        PREAMBLE = "PREAMBLE", "Preâmbulo"
        SUMMARY = "SUMMARY", "Resumo"
        TOC = "TOC", "Sumário"

        OBJECT_GROUP_INTRO = "OBJECT_GROUP_INTRO", "Texto comum do grupo de objetos"

        OBSERVATIONS = "OBSERVATIONS", "Observações"
        FINAL_CONSIDERATIONS = "FINAL_CONSIDERATIONS", "Considerações finais"
        CONCLUSION = "CONCLUSION", "Conclusão"

    SINGLETON_PLACEMENTS = {
        Placement.PREAMBLE,
        Placement.SUMMARY,
        Placement.TOC,
        Placement.OBSERVATIONS,
        Placement.FINAL_CONSIDERATIONS,
        Placement.CONCLUSION,
    }

    DEFAULT_TITLES = {
        Placement.PREAMBLE: "PREÂMBULO",
        Placement.SUMMARY: "RESUMO",
        Placement.TOC: "SUMÁRIO",
        Placement.OBSERVATIONS: "OBSERVAÇÕES",
        Placement.FINAL_CONSIDERATIONS: "CONSIDERAÇÕES FINAIS",
        Placement.CONCLUSION: "CONCLUSÃO",
    }

    NUMBERED_PLACEMENTS = {
        Placement.SUMMARY,
        Placement.OBSERVATIONS,
        Placement.FINAL_CONSIDERATIONS,
        Placement.CONCLUSION,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_case = models.ForeignKey(
        ReportCase,
        on_delete=models.CASCADE,
        related_name="text_blocks",
        verbose_name="Laudo",
    )

    placement = models.CharField(
        "Tipo do bloco",
        max_length=40,
        choices=Placement.choices,
        db_index=True,
    )

    group_key = models.CharField(
        "Chave do grupo",
        max_length=40,
        blank=False,
        default=GLOBAL_GROUP_KEY,
        db_index=True,
    )

    body = models.TextField("Texto")

    position = models.PositiveIntegerField(
        "Posição no laudo",
        default=0,
        db_index=True,
    )

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Texto do laudo"
        verbose_name_plural = "Textos do laudo"
        ordering = ["position", "created_at"]
        indexes = [
            models.Index(fields=["report_case", "position"]),
            models.Index(fields=["report_case", "placement", "group_key"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["report_case", "placement"],
                condition=Q(placement__in=[
                    "PREAMBLE",
                    "SUMMARY",
                    "TOC",
                    "OBSERVATIONS",
                    "FINAL_CONSIDERATIONS",
                    "CONCLUSION",
                ]),
                name="uq_report_textblock_singleton_per_placement",
            ),
            models.UniqueConstraint(
                fields=["report_case", "placement", "group_key"],
                condition=Q(placement="OBJECT_GROUP_INTRO"),
                name="uq_report_textblock_group_intro_per_key",
            ),
        ]

    @property
    def is_numbered(self) -> bool:
        """
        Indica se o bloco participa da numeração estrutural do laudo.
        """
        return self.placement in self.NUMBERED_PLACEMENTS

    @property
    def display_title(self) -> str:
        """
        Retorna o título a ser exibido no laudo, derivado do tipo do bloco.

        Para textos de grupo de objetos, o título é obtido a partir da chave
        do grupo. Para os demais, utiliza-se o título padrão do placement.
        """
        if self.placement == self.Placement.OBJECT_GROUP_INTRO:
            return (self.group_key or "").replace("_", " ").upper()

        return self.DEFAULT_TITLES.get(
            self.placement,
            self.get_placement_display().upper(),
        )

    def save(self, *args, **kwargs):
        """
        Normaliza o group_key e define automaticamente a posição do bloco no laudo.
        """
        if self.placement == self.Placement.OBJECT_GROUP_INTRO:
            self.group_key = (self.group_key or "").strip()
            if not self.group_key or self.group_key == self.GLOBAL_GROUP_KEY:
                raise ValueError(
                    "group_key obrigatório e não pode ser __GLOBAL__ para OBJECT_GROUP_INTRO."
                )
        else:
            self.group_key = self.GLOBAL_GROUP_KEY

        if not self.position:
            last_pos = (
                self.__class__.objects
                .filter(report_case=self.report_case)
                .aggregate(max_pos=Max("position"))
                .get("max_pos")
            )
            self.position = (last_pos or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_title
