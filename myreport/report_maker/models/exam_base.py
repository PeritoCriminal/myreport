from django.db import models

from .report_case import ReportCase


class ExamObject(models.Model):
    """
    Base abstrata para objetos de exame vinculados a um Laudo.

    Centraliza campos textuais comuns (descrição, metodologia, exame, resultados)
    e metadados de ordenação/auditoria, para reuso em tipos específicos
    (genérico, veículo, local, cadáver etc.).
    """

    report_case = models.ForeignKey(
        ReportCase,
        on_delete=models.CASCADE,
        related_name="objects",
        verbose_name="Laudo",
    )

    title = models.CharField("Título", max_length=160, blank=True)

    description = models.TextField("Descrição", blank=True)
    methodology = models.TextField("Metodologia", blank=True)
    examination = models.TextField("Exame", blank=True)
    results = models.TextField("Resultados", blank=True)

    order = models.PositiveIntegerField("Ordem", default=0)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["order", "id"]

    def __str__(self):
        return self.title or f"Objeto ({self.pk})"
