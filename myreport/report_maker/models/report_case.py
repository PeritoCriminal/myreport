import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def report_pdf_upload_path(instance, filename):
    """
    Define o caminho de upload do PDF final do laudo,
    agrupado pelo UUID do laudo.
    """
    return f"reports/{instance.id}/final/laudo_{instance.report_number}.pdf"


class ReportCase(models.Model):
    """
    Representa o Laudo Pericial, entidade central do exame,
    agregando objetos periciais, imagens e documento final.
    """

    class Objective(models.TextChoices):
        INITIAL_EXAM = "INITIAL_EXAM", "Exame inicial"
        COMPLEMENTARY_EXAM = "COMPLEMENTARY_EXAM", "Exame complementar"
        VEHICLE_EXAM = "VEHICLE_EXAM", "Exame em veículo automotor"
        SIMULATED_RECONSTRUCTION = "SIMULATED_RECONSTRUCTION", "Reprodução simulada"
        OTHER = "OTHER", "Outro"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        CLOSED = "CLOSED", "Concluído"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_number = models.CharField("Número do laudo", max_length=50, unique=True)
    protocol = models.CharField("Protocolo", max_length=50, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_cases",
        verbose_name="Autor",
    )

    objective = models.CharField(
        "Objetivo",
        max_length=40,
        choices=Objective.choices,
        default=Objective.INITIAL_EXAM,
    )

    requesting_authority = models.CharField("Autoridade requisitante", max_length=120)
    police_report = models.CharField("Boletim de ocorrência", max_length=60, blank=True)
    police_inquiry = models.CharField("Inquérito policial", max_length=60, blank=True)
    police_station = models.CharField("Distrito policial", max_length=120, blank=True)

    occurrence_datetime = models.DateTimeField("Data e hora da ocorrência", null=True, blank=True)
    assignment_datetime = models.DateTimeField("Data e hora da designação", null=True, blank=True)
    examination_datetime = models.DateTimeField("Data e hora do exame pericial", null=True, blank=True)

    photography_by = models.CharField("Fotografia", max_length=120, blank=True)
    sketch_by = models.CharField("Croqui", max_length=120, blank=True)

    conclusion = models.TextField("Conclusão", blank=True)

    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    is_locked = models.BooleanField("Bloqueado para edição", default=False)

    pdf_file = models.FileField(
        "PDF do laudo",
        upload_to=report_pdf_upload_path,
        null=True,
        blank=True,
    )

    concluded_at = models.DateTimeField("Concluído em", null=True, blank=True)

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Laudo"
        verbose_name_plural = "Laudos"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "updated_at"]),
        ]

    def __str__(self):
        return f"Laudo {self.report_number}"

    def clean(self):
        if self.status == self.Status.CLOSED:
            if not self.pdf_file:
                raise ValidationError("Laudo concluído deve possuir PDF.")
            if not self.is_locked:
                raise ValidationError("Laudo concluído deve estar bloqueado.")

    def close(self, pdf_file):
        """
        Finaliza o laudo, vinculando o PDF definitivo
        e impedindo novas edições.
        """
        self.pdf_file = pdf_file
        self.status = self.Status.CLOSED
        self.is_locked = True
        self.concluded_at = timezone.now()

    @property
    def can_edit(self):
        """
        Indica se o laudo pode ser editado.
        """
        return self.status == self.Status.OPEN and not self.is_locked
