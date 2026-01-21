# report_maker/models/report_case.py
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format

from institutions.models import Institution, Nucleus, Team


def report_pdf_upload_path(instance, filename):
    """
    Define o caminho de upload do PDF final do laudo,
    agrupado pelo UUID do laudo.
    """
    return f"reports/{instance.id}/final/laudo_{instance.report_number}.pdf"


def report_header_emblem_upload_path(instance, filename: str) -> str:
    """
    Caminho para armazenar snapshots de emblemas do cabeçalho do laudo.
    """
    return f"reports/{instance.id}/header/{filename}"


class ReportCase(models.Model):
    """
    Representa o Laudo Pericial, entidade central do exame,
    agregando objetos periciais, imagens e documento final.

    Histórico institucional por snapshot imutável:
    - Enquanto OPEN: exibe dados via FKs (Institution/Nucleus/Team).
    - Ao fechar (close): congela snapshots no BD.
    - Após CLOSED: exibe exclusivamente snapshots (imutável).
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
    # Organization snapshot (imutável) — congelado SOMENTE no fechamento
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

    # ---------------------------------------------------------------------
    # Header snapshot (imutável) — congelado SOMENTE no fechamento
    # ---------------------------------------------------------------------
    emblem_primary_snapshot = models.ImageField(
        "Emblema primário (snapshot)",
        upload_to=report_header_emblem_upload_path,
        null=True,
        blank=True,
    )
    emblem_secondary_snapshot = models.ImageField(
        "Emblema secundário (snapshot)",
        upload_to=report_header_emblem_upload_path,
        null=True,
        blank=True,
    )
    honoree_title_snapshot = models.CharField(
        "Título do homenageado (snapshot)",
        max_length=60,
        blank=True,
        default="",
    )
    honoree_name_snapshot = models.CharField(
        "Nome do homenageado (snapshot)",
        max_length=120,
        blank=True,
        default="",
    )
    institution_kind_snapshot = models.CharField(
        "Kind institucional (snapshot)",
        max_length=120,
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
    criminal_typification = models.CharField(
        "Tipificação penal",
        max_length=80,
        blank=True,
        help_text="Ex.: furto, roubo, homicídio, latrocínio",
    )

    occurrence_datetime = models.DateTimeField("Data e hora da ocorrência", null=True, blank=True)
    assignment_datetime = models.DateTimeField("Data e hora da designação", null=True, blank=True)
    examination_datetime = models.DateTimeField("Data e hora do exame pericial", null=True, blank=True)

    photography_by = models.CharField("Fotografia", max_length=120, blank=True)
    sketch_by = models.CharField("Croqui", max_length=120, blank=True)

    # conclusion = models.TextField("Conclusão", blank=True)

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
    # Frozen flag
    # ---------------------------------------------------------------------
    @property
    def is_frozen(self) -> bool:
        """
        Verdadeiro apenas após o congelamento (close()).
        """
        return bool(self.organization_frozen_at)

    # ---------------------------------------------------------------------
    # Organization snapshot API
    # ---------------------------------------------------------------------
    def freeze_organization_snapshot(self, force: bool = False) -> None:
        """
        Congela a organização do laudo, copiando dados atuais para os snapshots.

        Regras:
        - Se já estiver congelado, não faz nada (a menos que force=True).
        - O congelamento ocorre SOMENTE no fechamento do laudo (close()).
        """
        if self.organization_frozen_at and not force:
            return

        # ─────────────────────────────────────────────
        # Snapshots de organização (texto)
        # ─────────────────────────────────────────────
        if self.institution:
            self.institution_acronym_snapshot = self.institution.acronym or ""
            self.institution_name_snapshot = self.institution.name or ""
        else:
            self.institution_acronym_snapshot = ""
            self.institution_name_snapshot = ""

        self.nucleus_name_snapshot = self.nucleus.name if self.nucleus else ""
        self.team_name_snapshot = self.team.name if self.team else ""

        # ─────────────────────────────────────────────
        # Snapshots do cabeçalho (emblemas / honraria / kind)
        # ─────────────────────────────────────────────
        if self.institution:
            self.emblem_primary_snapshot = getattr(self.institution, "emblem_primary", None)
            self.emblem_secondary_snapshot = getattr(self.institution, "emblem_secondary", None)

            self.honoree_title_snapshot = getattr(self.institution, "honoree_title", "") or ""
            self.honoree_name_snapshot = getattr(self.institution, "honoree_name", "") or ""

            # kind pode ser choice; guardamos texto bruto (string) como snapshot
            self.institution_kind_snapshot = str(getattr(self.institution, "kind", "") or "")
        else:
            self.emblem_primary_snapshot = None
            self.emblem_secondary_snapshot = None
            self.honoree_title_snapshot = ""
            self.honoree_name_snapshot = ""
            self.institution_kind_snapshot = ""

        self.organization_frozen_at = timezone.now()

    # ---------------------------------------------------------------------
    # Display helpers (OPEN -> FK, CLOSED -> snapshot)
    # ---------------------------------------------------------------------
    @property
    def institution_name_for_display(self) -> str:
        if self.is_frozen:
            return self.institution_name_snapshot or ""
        return (self.institution.name if self.institution else "") or ""

    @property
    def institution_acronym_for_display(self) -> str:
        if self.is_frozen:
            return self.institution_acronym_snapshot or ""
        return (self.institution.acronym if self.institution else "") or ""

    @property
    def institution_display(self) -> str:
        """
        Texto institucional para exibição/geração (HTML/PDF/DOCX).

        OPEN: via FK atual
        CLOSED: via snapshot
        """
        name = self.institution_name_for_display
        acr = self.institution_acronym_for_display
        if name and acr:
            return f"{name} ({acr})"
        return name or acr

    @property
    def nucleus_display(self) -> str:
        if self.is_frozen:
            return self.nucleus_name_snapshot or ""
        return (self.nucleus.name if self.nucleus else "") or ""

    @property
    def team_display(self) -> str:
        if self.is_frozen:
            return self.team_name_snapshot or ""
        return (self.team.name if self.team else "") or ""

    # ---------------------------------------------------------------------
    # Header helper (OPEN -> FK, CLOSED -> snapshot)
    # ---------------------------------------------------------------------
    @property
    def header_context(self) -> dict:
        """
        Contexto do cabeçalho do laudo (HTML/PDF/DOCX).

        OPEN: dados via FKs (cadastro atual)
        CLOSED: dados via snapshot (imutável)
        """
        inst = self.institution  # FK continua sendo a fonte dos emblemas

        if self.is_frozen:
            name = self.institution_name_snapshot or ""
            acronym = self.institution_acronym_snapshot or ""
            hon_title = self.honoree_title_snapshot or ""
            hon_name = self.honoree_name_snapshot or ""
            kind_display = self.institution_kind_snapshot or ""

            # 🔹 Emblemas: snapshot se existir, senão fallback para Institution
            emblem_primary = self.emblem_primary_snapshot or (inst.emblem_primary if inst else None)
            emblem_secondary = self.emblem_secondary_snapshot or (inst.emblem_secondary if inst else None)

        else:
            name = (inst.name if inst else "") or ""
            acronym = (inst.acronym if inst else "") or ""
            hon_title = (getattr(inst, "honoree_title", "") if inst else "") or ""
            hon_name = (getattr(inst, "honoree_name", "") if inst else "") or ""

            if inst and hasattr(inst, "get_kind_display"):
                kind_display = inst.get_kind_display()
            else:
                kind_display = str(getattr(inst, "kind", "") or "") if inst else ""

            emblem_primary = inst.emblem_primary if (inst and inst.emblem_primary) else None
            emblem_secondary = inst.emblem_secondary if (inst and inst.emblem_secondary) else None

        honoree_line = ""
        if hon_title and hon_name:
            honoree_line = f"{hon_title} {hon_name}"
        elif hon_name:
            honoree_line = hon_name

        # 🔹 unit_line: respeita snapshot se frozen, senão FKs
        if self.is_frozen:
            unit_line = " - ".join(
                p for p in [self.nucleus_display, self.team_display] if p
            )
        else:
            nucleus_name = self.nucleus.name if self.nucleus else ""
            team_name = self.team.name if self.team else ""
            unit_line = " - ".join(p for p in [nucleus_name, team_name] if p)

        return {
            "name": name or None,
            "acronym": acronym or None,
            "kind_display": kind_display or None,
            "honoree_line": honoree_line or None,
            "unit_line": unit_line or None,
            "emblem_primary": emblem_primary,
            "emblem_secondary": emblem_secondary,
        }


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

        - Permite o PRIMEIRO congelamento (quando organization_frozen_at era NULL no banco).
        - Bloqueia qualquer alteração posterior.
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
            "emblem_primary_snapshot",
            "emblem_secondary_snapshot",
            "honoree_title_snapshot",
            "honoree_name_snapshot",
            "institution_kind_snapshot",
            "organization_frozen_at",
        ).first()

        if not old:
            return

        # ✅ Se ainda NÃO estava congelado no banco, permitir salvar (inclusive no momento do close()).
        if old["organization_frozen_at"] is None:
            return

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
            or old["honoree_title_snapshot"] != self.honoree_title_snapshot
            or old["honoree_name_snapshot"] != self.honoree_name_snapshot
            or old["institution_kind_snapshot"] != self.institution_kind_snapshot
            or old["organization_frozen_at"] != self.organization_frozen_at
        )

        # ImageField: compara pelo "name" (path)
        emb_primary_old = old["emblem_primary_snapshot"] or ""
        emb_secondary_old = old["emblem_secondary_snapshot"] or ""
        emb_primary_new = (self.emblem_primary_snapshot.name if self.emblem_primary_snapshot else "") or ""
        emb_secondary_new = (self.emblem_secondary_snapshot.name if self.emblem_secondary_snapshot else "") or ""

        emblems_changed = (emb_primary_old != emb_primary_new) or (emb_secondary_old != emb_secondary_new)

        if fk_changed or snapshot_changed or emblems_changed:
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

        # Congelamento no ato de finalização
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

    @staticmethod
    def _gendered_roles_from_name(name: str, masculine: str, feminine: str, neutral: str) -> str:
        """
        Retorna a forma de tratamento conforme 'Dr.'/'Dra.' no início do nome.
        """
        if not name:
            return neutral
        n = name.strip().lower()
        if n.startswith("dra.") or n.startswith("dra "):
            return feminine
        if n.startswith("dr.") or n.startswith("dr "):
            return masculine
        return neutral

    @property
    def preamble(self) -> str:
        """
        Preâmbulo institucional do laudo (modelo inspirado no sistema legado).

        - Usa snapshots quando congelado.
        - Usa data da designação (assignment_datetime) quando existir.
        - Mantém redação objetiva no passado simples.
        """
        examiner = (
            getattr(self.author, "report_signature_name", "")
            or getattr(self.author, "display_name", "")
            or str(self.author)
        )

        authority = self.requesting_authority or ""

        if self.assignment_datetime:
            full_date = date_format(
                self.assignment_datetime.date(),
                format="j \\d\\e F \\d\\e Y",
                use_l10n=True,
            ).lower()
        else:
            full_date = ""

        inst = self.institution_display
        nuc = self.nucleus_display
        team = self.team_display

        d_examiner = self._gendered_roles_from_name(
            examiner,
            masculine="foi designado o Perito Criminal",
            feminine="foi designada a Perita Criminal",
            neutral="foi designado o Perito Criminal",
        )
        d_authority = self._gendered_roles_from_name(
            authority,
            masculine="pelo Exmo. Sr. Delegado de Polícia",
            feminine="pela Exma. Sra. Delegada de Polícia",
            neutral="pelo(a) Exmo(a). Sr(a). Delegado(a) de Polícia",
        )

        org_parts = [p for p in [inst, nuc, team] if p]
        org_text = " / ".join(org_parts)

        if full_date and org_text:
            return (
                f"Aos {full_date}, em conformidade com o disposto no artigo 178 do Decreto-Lei nº 3.689, "
                f"de 3 de outubro de 1941, {d_examiner} {examiner} para proceder ao exame pericial "
                f"no âmbito de {org_text}, em atendimento à requisição expedida {d_authority} {authority}."
            )

        if full_date:
            return (
                f"Aos {full_date}, em conformidade com o disposto no artigo 178 do Decreto-Lei nº 3.689, "
                f"de 3 de outubro de 1941, {d_examiner} {examiner} para proceder ao exame pericial "
                f"em atendimento à requisição expedida {d_authority} {authority}."
            )

        return (
            f"Em conformidade com o disposto no artigo 178 do Decreto-Lei nº 3.689, de 3 de outubro de 1941, "
            f"{d_examiner} {examiner} para proceder ao exame pericial "
            f"em atendimento à requisição expedida {d_authority} {authority}."
        )
