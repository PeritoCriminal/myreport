# report_maker/models/report_case.py
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from institutions.models import Institution, Nucleus, Team


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

    Este modelo também preserva HISTÓRICO institucional por meio de snapshot imutável:
    - Institution / Nucleus / Team são referenciados por FK (para filtros e navegação);
    - Nomes e siglas são copiados para campos snapshot (para manter consistência histórica),
      evitando que renomeações futuras alterem a exibição de laudos antigos.
    """

    # ---------------------------------------------------------------------
    # Choices
    # ---------------------------------------------------------------------
    class Objective(models.TextChoices):
        INITIAL_EXAM = "INITIAL_EXAM", "Exame inicial"
        COMPLEMENTARY_EXAM = "COMPLEMENTARY_EXAM", "Exame complementar"
        VEHICLE_EXAM = "VEHICLE_EXAM", "Exame em veículo automotor"
        SIMULATED_RECONSTRUCTION = "SIMULATED_RECONSTRUCTION", "Reprodução simulada"
        OTHER = "OTHER", "Outro"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        CLOSED = "CLOSED", "Concluído"

    # ---------------------------------------------------------------------
    # Identity / authorship
    # ---------------------------------------------------------------------
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_number = models.CharField("Número do laudo", max_length=50, unique=True)
    protocol = models.CharField("Protocolo", max_length=50, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_cases",
        verbose_name="Autor",
    )

    # ---------------------------------------------------------------------
    # Organization (FK) — filtros, navegação e permissões futuras
    # ---------------------------------------------------------------------
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="report_cases",
        verbose_name="Instituição",
        null=True,
        blank=True,
    )

    nucleus = models.ForeignKey(
        Nucleus,
        on_delete=models.PROTECT,
        related_name="report_cases",
        verbose_name="Núcleo",
        null=True,
        blank=True,
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="report_cases",
        verbose_name="Equipe",
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------------------
    # Organization snapshot (imutável) — consistência histórica de exibição
    # ---------------------------------------------------------------------
    institution_acronym_snapshot = models.CharField(
        "Sigla da instituição (snapshot)",
        max_length=30,
        blank=True,
        default="",
    )
    institution_name_snapshot = models.CharField(
        "Nome da instituição (snapshot)",
        max_length=255,
        blank=True,
        default="",
    )
    nucleus_name_snapshot = models.CharField(
        "Nome do núcleo (snapshot)",
        max_length=255,
        blank=True,
        default="",
    )
    team_name_snapshot = models.CharField(
        "Nome da equipe (snapshot)",
        max_length=255,
        blank=True,
        default="",
    )
    organization_frozen_at = models.DateTimeField(
        "Organização congelada em",
        null=True,
        blank=True,
        db_index=True,
    )

    # ---------------------------------------------------------------------
    # Report metadata
    # ---------------------------------------------------------------------
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

    # ---------------------------------------------------------------------
    # Django meta
    # ---------------------------------------------------------------------
    class Meta:
        verbose_name = "Laudo"
        verbose_name_plural = "Laudos"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["organization_frozen_at", "updated_at"]),
        ]

    def __str__(self):
        return f"Laudo {self.report_number}"

    # ---------------------------------------------------------------------
    # Organization snapshot API
    # ---------------------------------------------------------------------
    def freeze_organization_snapshot(self, force: bool = False) -> None:
        """
        Congela a organização do laudo, copiando dados atuais para os snapshots.

        Regras:
        - Se já estiver congelado, não faz nada (a menos que force=True).
        - O congelamento deve ocorrer no momento da FINALIZAÇÃO do laudo,
          garantindo que o histórico não seja alterado por renomeações futuras.
        """
        if self.organization_frozen_at and not force:
            return

        if self.institution:
            self.institution_acronym_snapshot = self.institution.acronym
            self.institution_name_snapshot = self.institution.name
        else:
            self.institution_acronym_snapshot = ""
            self.institution_name_snapshot = ""

        self.nucleus_name_snapshot = self.nucleus.name if self.nucleus else ""
        self.team_name_snapshot = self.team.name if self.team else ""

        self.organization_frozen_at = timezone.now()

    # ---------------------------------------------------------------------
    # Display helpers (priorizam snapshot quando existir)
    # ---------------------------------------------------------------------
    @property
    def institution_display(self) -> str:
        """
        Texto institucional para exibição/geração (HTML/PDF/DOCX).

        Prioridade:
        1) snapshot (histórico)
        2) FK atual (rascunho)
        """
        if self.institution_acronym_snapshot or self.institution_name_snapshot:
            if self.institution_acronym_snapshot and self.institution_name_snapshot:
                return f"{self.institution_acronym_snapshot} - {self.institution_name_snapshot}"
            return self.institution_acronym_snapshot or self.institution_name_snapshot

        if self.institution:
            return f"{self.institution.acronym} - {self.institution.name}"

        return ""

    @property
    def nucleus_display(self) -> str:
        if self.nucleus_name_snapshot:
            return self.nucleus_name_snapshot
        return self.nucleus.name if self.nucleus else ""

    @property
    def team_display(self) -> str:
        if self.team_name_snapshot:
            return self.team_name_snapshot
        return self.team.name if self.team else ""

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    def _validate_close_requirements(self) -> None:
        """
        Regras mínimas para laudo concluído:
        - precisa ter PDF
        - precisa estar bloqueado
        """
        if self.status == self.Status.CLOSED:
            if not self.pdf_file:
                raise ValidationError("Laudo concluído deve possuir PDF.")
            if not self.is_locked:
                raise ValidationError("Laudo concluído deve estar bloqueado.")

    def _validate_organization_consistency(self) -> None:
        """
        Garante consistência entre Institution / Nucleus / Team.
        """
        if self.team and self.nucleus and self.team.nucleus_id != self.nucleus_id:
            raise ValidationError("A equipe selecionada não pertence ao núcleo informado.")

        if self.nucleus and self.institution and self.nucleus.institution_id != self.institution_id:
            raise ValidationError("O núcleo selecionado não pertence à instituição informada.")

        if self.team and self.institution and self.team.nucleus.institution_id != self.institution_id:
            raise ValidationError("A equipe selecionada não pertence à instituição informada.")

    def _validate_organization_immutability(self) -> None:
        """
        Se a organização já estava congelada no BANCO, impede alterações.

        Regra importante:
        - Permite o PRIMEIRO congelamento (quando organization_frozen_at ainda era NULL no banco).
        - Bloqueia qualquer alteração posterior, preservando o histórico.
        """
        if not self.pk:
            return

        old = type(self).objects.filter(pk=self.pk).values(
            "institution_id",
            "nucleus_id",
            "team_id",
            "institution_acronym_snapshot",
            "institution_name_snapshot",
            "nucleus_name_snapshot",
            "team_name_snapshot",
            "organization_frozen_at",
        ).first()

        if not old:
            return

        # ✅ Se ainda NÃO estava congelado no banco, estamos no "primeiro freeze" — permitir.
        if old["organization_frozen_at"] is None:
            return

        # A partir daqui, o laudo JÁ estava congelado: qualquer mudança é proibida.
        fk_changed = (
            old["institution_id"] != self.institution_id
            or old["nucleus_id"] != self.nucleus_id
            or old["team_id"] != self.team_id
        )

        snapshot_changed = (
            old["institution_acronym_snapshot"] != self.institution_acronym_snapshot
            or old["institution_name_snapshot"] != self.institution_name_snapshot
            or old["nucleus_name_snapshot"] != self.nucleus_name_snapshot
            or old["team_name_snapshot"] != self.team_name_snapshot
            or old["organization_frozen_at"] != self.organization_frozen_at
        )

        if fk_changed or snapshot_changed:
            raise ValidationError("A organização deste laudo foi congelada e não pode ser alterada.")


    def clean(self):
        """
        Valida regras de negócio centrais do laudo.
        """
        self._validate_close_requirements()
        self._validate_organization_consistency()
        self._validate_organization_immutability()

    # ---------------------------------------------------------------------
    # Domain operation
    # ---------------------------------------------------------------------
    def close(self, pdf_file):
        """
        Finaliza o laudo, vinculando o PDF definitivo e impedindo novas edições.

        Efeito colateral desejado:
        - congela a organização (snapshot) no momento da conclusão,
          mantendo histórico imutável.
        """
        self.pdf_file = pdf_file
        self.status = self.Status.CLOSED
        self.is_locked = True
        self.concluded_at = timezone.now()

        # Congelamento no ato de finalização (ponto de verdade do histórico)
        self.freeze_organization_snapshot()

    @property
    def can_edit(self):
        """
        Indica se o laudo pode ser editado.
        """
        return self.status == self.Status.OPEN and not self.is_locked

    # ---------------------------------------------------------------------
    # Save hook
    # ---------------------------------------------------------------------
    def save(self, *args, **kwargs):
        """
        Garante validações e integridade do modelo antes de persistir.
        """
        self.full_clean()
        super().save(*args, **kwargs)
