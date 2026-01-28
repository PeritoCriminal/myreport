# report_maker/models/report_text_block.py
import uuid
from django.db import models
from django.db.models import Max, Q
from .report_case import ReportCase


class ReportTextBlock(models.Model):
    class Placement(models.TextChoices):
        PREAMBLE = "PREAMBLE", "Preâmbulo"
        SUMMARY = "SUMMARY", "Resumo"
        TOC = "TOC", "Sumário"

        OBJECT_GROUP_INTRO = "OBJECT_GROUP_INTRO", "Texto comum do grupo de objetos"

        OBSERVATIONS = "OBSERVATIONS", "Observações"
        FINAL_CONSIDERATIONS = "FINAL_CONSIDERATIONS", "Considerações finais"
        CONCLUSION = "CONCLUSION", "Conclusão"

    # Placements que só podem existir 0..1 por laudo
    SINGLETON_PLACEMENTS = {
        Placement.PREAMBLE,
        Placement.SUMMARY,
        Placement.TOC,
        Placement.OBSERVATIONS,
        Placement.FINAL_CONSIDERATIONS,
        Placement.CONCLUSION,
    }

    # Títulos padrão (se title vier vazio, você injeta isso)
    DEFAULT_TITLES = {
        Placement.PREAMBLE: "PREÂMBULO",
        Placement.SUMMARY: "RESUMO",
        Placement.TOC: "SUMÁRIO",
        Placement.OBSERVATIONS: "OBSERVAÇÕES",
        Placement.FINAL_CONSIDERATIONS: "CONSIDERAÇÕES FINAIS",
        Placement.CONCLUSION: "CONCLUSÃO",
    }

    # Define se entra na numeração T1 (preâmbulo normalmente não)
    NUMBERED_PLACEMENTS = {
        Placement.SUMMARY,
        Placement.OBSERVATIONS,
        Placement.FINAL_CONSIDERATIONS,
        Placement.CONCLUSION,
        # TOC: escolha sua (muitos deixam sem número)
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

    # para OBJECT_GROUP_INTRO (um texto por tipo de objeto/grupo)
    group_key = models.CharField(
        "Chave do grupo",
        max_length=40,
        blank=True,
        db_index=True,
        help_text="Usado apenas em 'Texto comum do grupo de objetos'. Ex.: LOCATIONS, VEHICLES...",
    )

    title = models.CharField("Título", max_length=160, blank=True)
    body = models.TextField("Texto", blank=True)

    # ordem GLOBAL no laudo (é isso que vai guiar a numeração/posição)
    position = models.PositiveIntegerField("Posição no laudo", default=0, db_index=True)

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
            # 0..1 por laudo para os singletons
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
            # 0..1 por grupo (só quando for OBJECT_GROUP_INTRO)
            models.UniqueConstraint(
                fields=["report_case", "placement", "group_key"],
                condition=Q(placement="OBJECT_GROUP_INTRO"),
                name="uq_report_textblock_group_intro_per_key",
            ),
        ]

    @property
    def is_numbered(self) -> bool:
        return self.placement in self.NUMBERED_PLACEMENTS

    def save(self, *args, **kwargs):
        # título default
        if not (self.title or "").strip():
            self.title = self.DEFAULT_TITLES.get(self.placement, "")

        # garante group_key onde precisa e limpa onde não precisa
        if self.placement == self.Placement.OBJECT_GROUP_INTRO:
            self.group_key = (self.group_key or "").strip()
        else:
            self.group_key = ""

        # auto-position global por laudo
        if not self.position:
            last_pos = (
                self.__class__.objects.filter(report_case=self.report_case)
                .aggregate(max_pos=Max("position"))
                .get("max_pos")
            )
            self.position = (last_pos or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        t = (self.title or "").strip()
        return t or f"Texto ({self.get_placement_display()})"
