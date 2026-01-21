# report_maker/models/report_text_block.py
import uuid

from django.db import models
from django.db.models import Max

from .report_case import ReportCase


class ReportTextBlock(models.Model):
    class Placement(models.TextChoices):
        # Permite substituir/ignorar o preâmbulo gerado pelo sistema
        PREAMBLE = "PREAMBLE", "Preâmbulo (substituto do sistema)"

        AFTER_PREAMBLE = "AFTER_PREAMBLE", "Após preâmbulo"

        # Texto geral antes de qualquer objeto
        BEFORE_OBJECTS = "BEFORE_OBJECTS", "Antes dos objetos de exame (geral)"

        # Texto introdutório específico
        LOCATIONS_INTRO = "LOCATIONS_INTRO", "Locais – texto introdutório"

        # ⚠️ Hoje funciona como INTRO de objetos genéricos (fallback):
        # objetos ainda não tipificados em classes específicas
        # (ex.: cadáveres, armas, munições, facas etc., quando existirem classes próprias)
        VEHICLES_INTRO = "VEHICLES_INTRO", "Objetos genéricos – texto introdutório"

        AFTER_OBJECTS = "AFTER_OBJECTS", "Após os objetos de exame"

        FINAL_CONSIDERATIONS = "FINAL_CONSIDERATIONS", "Considerações finais"
        CONCLUSION = "CONCLUSION", "Conclusão"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_case = models.ForeignKey(
        ReportCase,
        on_delete=models.CASCADE,
        related_name="text_blocks",
        verbose_name="Laudo",
    )

    placement = models.CharField(
        "Posição no laudo",
        max_length=40,
        choices=Placement.choices,
        default=Placement.AFTER_PREAMBLE,
        db_index=True,
    )

    title = models.CharField("Título", max_length=160, blank=True)

    body = models.TextField("Texto", blank=True)

    order = models.PositiveIntegerField("Ordem", default=0)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Texto do laudo"
        verbose_name_plural = "Textos do laudo"
        ordering = ["placement", "order", "created_at"]
        indexes = [
            models.Index(fields=["report_case", "placement", "order"]),
        ]

    def save(self, *args, **kwargs):
        # auto-order (1..N) por (laudo + placement) quando vier 0
        if not self.order:
            last_order = (
                self.__class__.objects.filter(
                    report_case=self.report_case,
                    placement=self.placement,
                )
                .aggregate(max_order=Max("order"))
                .get("max_order")
            )
            self.order = (last_order or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        t = (self.title or "").strip()
        return t or f"Texto ({self.get_placement_display()})"
