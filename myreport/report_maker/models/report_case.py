# report_maker/models/report_case.py
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format

from institutions.models import Institution, Nucleus, Team

def report_pdf_upload_path(instance, filename: str) -> str:
    """
    Mantida por compatibilidade com migrações antigas.
    NÃO é mais usada no modelo atual (pdf_file foi removido).
    """
    return f"reports/{instance.id}/final/{filename}"


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
    - Ao fechar (close): congela snapshots no BD (incluindo cópia REAL dos emblemas).
    - Após congelar: exibe exclusivamente snapshots (imutável).
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
    city_name_snapshot = models.CharField(
        "Nome da Cidade (snapshot)",
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
        "Objetivo (tipo)",
        max_length=40,
        choices=Objective.choices,
        blank=True,
        default="",
    )

    objective_text = models.CharField(
        "Objetivo (descrição livre)",
        max_length=255,
        blank=True,
        default="",
    )

    requesting_authority = models.CharField("Autoridade requisitante", max_length=120)
    police_report = models.CharField("Boletim de ocorrência", max_length=60, blank=True)
    police_inquiry = models.CharField("Inquérito policial", max_length=60, blank=True)
    police_station = models.CharField("Distrito policial", max_length=120, blank=True)
    criminal_typification = models.CharField(
        "Tipificação penal / Ocorrência",
        max_length=80,
        blank=True,
        help_text="Ex.: furto, roubo, homicídio, latrocínio",
    )

    occurrence_datetime = models.DateTimeField("Data e hora da ocorrência", null=True, blank=True)
    assignment_datetime = models.DateTimeField("Data e hora da designação", null=True, blank=True)
    examination_datetime = models.DateTimeField("Data e hora do exame pericial", null=True, blank=True)

    photography_by = models.CharField("Fotografia", max_length=120, blank=True)
    sketch_by = models.CharField("Croqui", max_length=120, blank=True)

    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )

    is_locked = models.BooleanField("Bloqueado para edição", default=False)

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
    # Snapshot helpers
    # ---------------------------------------------------------------------
    def _snapshot_image_once(self, src_field, dst_attr: str, filename_prefix: str) -> None:
        """
        Cria snapshot REAL do arquivo (cópia), salvando no ImageField de destino.

        Regras:
        - Só deve ser chamado quando ainda NÃO estiver congelado.
        - Não apaga arquivo antigo e não regrava (congelar só uma vez).
        - save=False para permitir que o fluxo salve o model no final.
        """
        if not src_field:
            setattr(self, dst_attr, None)
            return

        src_name = getattr(src_field, "name", "") or ""
        _, ext = os.path.splitext(src_name)
        ext = ext.lower() if ext else ".png"

        new_name = f"{filename_prefix}{ext}"

        src_field.open("rb")
        try:
            content = src_field.read()
        finally:
            src_field.close()

        snapshot_field = getattr(self, dst_attr)
        snapshot_field.save(new_name, ContentFile(content), save=False)

    # ---------------------------------------------------------------------
    # Organization snapshot API
    # ---------------------------------------------------------------------
    def freeze_organization_snapshot(self) -> None:
        """
        Congela a organização do laudo, copiando dados atuais para snapshots.

        Regras:
        - Se já estiver congelado, não faz nada.
        - O congelamento ocorre SOMENTE no fechamento do laudo (close()).
        - Emblemas são copiados (snapshot REAL), e não apenas referenciados.
        """
        if self.organization_frozen_at:
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
        # Snapshots do cabeçalho (honraria / kind)
        # ─────────────────────────────────────────────
        inst = self.institution
        if inst:
            self.honoree_title_snapshot = getattr(inst, "honoree_title", "") or ""
            self.honoree_name_snapshot = getattr(inst, "honoree_name", "") or ""

            self.institution_kind_snapshot = (
                inst.get_kind_display()
                if hasattr(inst, "get_kind_display")
                else str(getattr(inst, "kind", "") or "")
            )

            # Emblemas: cópia real no storage do laudo
            self._snapshot_image_once(
                src_field=getattr(inst, "emblem_primary", None),
                dst_attr="emblem_primary_snapshot",
                filename_prefix="emblem_primary_snapshot",
            )
            self._snapshot_image_once(
                src_field=getattr(inst, "emblem_secondary", None),
                dst_attr="emblem_secondary_snapshot",
                filename_prefix="emblem_secondary_snapshot",
            )
        else:
            self.honoree_title_snapshot = ""
            self.honoree_name_snapshot = ""
            self.institution_kind_snapshot = ""
            self.emblem_primary_snapshot = None
            self.emblem_secondary_snapshot = None

        self.organization_frozen_at = timezone.now()

        if self.nucleus and self.nucleus.city:
            self.city_name_snapshot = self.nucleus.city.name


    # ---------------------------------------------------------------------
    # Display helpers (OPEN -> FK, CLOSED -> snapshot) + metadata do laudo
    # ---------------------------------------------------------------------
    def get_render_blocks(self) -> list[dict]:
        """
        Blocos iniciais do laudo (sem numeração).
        A view/builder decide numeração (T1/T2/T3...).
        """
        return [
            {
                "kind": "kv_section",
                "label": "Dados da Requisição",
                "items": [
                    {"label": "Autoridade requisitante", "value": self.requesting_authority},
                    {"label": "Inquérito policial", "value": self.police_inquiry},
                    {"label": "Distrito policial", "value": self.police_station},
                    {"label": "Boletim de ocorrência", "value": self.police_report},
                    {"label": "Tipificação penal / Ocorrência", "value": self.criminal_typification},
                    {"label": "Data e hora da ocorrência", "value": self.occurrence_datetime},
                ],
            },
            {
                "kind": "kv_section",
                "label": "Dados do Atendimento",
                "items": [
                    {"label": "Protocolo de atendimento", "value": self.protocol},
                    {"label": "Data e hora do exame pericial", "value": self.examination_datetime},
                    {"label": "Perito", "value": self.report_identity_name},
                    {"label": "Fotografia", "value": self.photography_by},
                    {"label": "Croqui", "value": self.sketch_by},
                ],
            },
            {
                "kind": "text_section",
                "label": "Objetivo",
                "value": self.objective_for_display,
                "fmt": "text",
            },
        ]

    @property
    def objective_for_display(self) -> str:
        text = (self.objective_text or "").strip()
        if text:
            return text
        return self.get_objective_display() if self.objective else ""

    @property
    def report_identity_name(self) -> str:
        return (
            getattr(self.author, "report_signature_name", "")
            or getattr(self.author, "display_name", "")
            or str(self.author)
        )

    @property
    def report_metadata_context(self) -> dict:
        return {
            "requisition": {
                "requesting_authority": self.requesting_authority,
                "police_inquiry": self.police_inquiry,
                "police_station": self.police_station,
                "police_report": self.police_report,
                "criminal_typification": self.criminal_typification,
                "occurrence_datetime": self.occurrence_datetime,
            },
            "service": {
                "protocol": self.protocol,
                "examination_datetime": self.examination_datetime,
                "author_name": self.report_identity_name,
                "photography_by": self.photography_by,
                "sketch_by": self.sketch_by,
            },
            "objective": {
                "objective_text": self.objective_for_display,
            },
        }

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
        return f"{name} ({acr})" if (name and acr) else (name or acr)

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
        inst = self.institution

        if self.is_frozen:
            name = self.institution_name_snapshot or ""
            acronym = self.institution_acronym_snapshot or ""
            hon_title = self.honoree_title_snapshot or ""
            hon_name = self.honoree_name_snapshot or ""
            kind_display = self.institution_kind_snapshot or ""

            emblem_primary = self.emblem_primary_snapshot
            emblem_secondary = self.emblem_secondary_snapshot
        else:
            name = (inst.name if inst else "") or ""
            acronym = (inst.acronym if inst else "") or ""
            hon_title = (getattr(inst, "honoree_title", "") if inst else "") or ""
            hon_name = (getattr(inst, "honoree_name", "") if inst else "") or ""

            kind_display = (
                inst.get_kind_display()
                if (inst and hasattr(inst, "get_kind_display"))
                else (str(getattr(inst, "kind", "") or "") if inst else "")
            )

            emblem_primary = inst.emblem_primary if (inst and getattr(inst, "emblem_primary", None)) else None
            emblem_secondary = inst.emblem_secondary if (inst and getattr(inst, "emblem_secondary", None)) else None

        honoree_line = f"{hon_title} {hon_name}".strip() if (hon_title and hon_name) else (hon_name or "")

        unit_line = " - ".join(p for p in [self.nucleus_display, self.team_display] if p)

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
        - precisa estar bloqueado
        - precisa ter organização definida (para congelar snapshot)
        """
        if self.status == self.Status.CLOSED:
            if not self.is_locked:
                raise ValidationError("Laudo concluído deve estar bloqueado.")

            if not self.institution_id:
                raise ValidationError("Informe a instituição antes de concluir o laudo.")
            if not self.nucleus_id:
                raise ValidationError("Informe o núcleo antes de concluir o laudo.")
            if not self.team_id:
                raise ValidationError("Informe a equipe antes de concluir o laudo.")

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
        super().clean()

        if self.objective == self.Objective.OTHER and not (self.objective_text or "").strip():
            raise ValidationError({"objective_text": "Informe o objetivo quando selecionado 'Outro'."})

        self._validate_close_requirements()
        self._validate_organization_immutability()

    # ---------------------------------------------------------------------
    # Domain operation
    # ---------------------------------------------------------------------
    def close(self):
        """
        Finaliza o laudo, impedindo novas edições e congelando a organização (snapshot).
        """
        # congelar ANTES de setar CLOSED (pra garantir snapshot preenchido)
        self.freeze_organization_snapshot()

        self.status = self.Status.CLOSED
        self.is_locked = True
        self.concluded_at = timezone.now()

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
        Preâmbulo institucional do laudo.
        
        - Utiliza snapshots de cidade e organização quando o laudo está congelado.
        - Remove separadores '/' para garantir uma redação fluida e formal.
        """
        # 1. Identificação do Perito e Autoridade
        examiner = self.report_identity_name
        authority = self.requesting_authority or ""

        # 2. Data da Designação
        date_text = ""
        if self.assignment_datetime:
            full_date = date_format(
                self.assignment_datetime.date(),
                format="j \\d\\e F \\d\\e Y",
                use_l10n=True,
            ).lower()
            date_text = f"Aos {full_date}, "

        # 3. Cidade (Snapshot ou Atual)
        # Se estiver congelado, usa o snapshot; se não, tenta buscar no Nucleus.
        city_name = self.city_name_snapshot if self.is_frozen else (
            self.nucleus.city.name if (self.nucleus and self.nucleus.city) else ""
        )
        city_prefix = f"na cidade de {city_name} e " if city_name else ""

        # 4. Estrutura Institucional (Fluida)
        # Utilizamos as propriedades de display que já tratam a lógica de snapshot internamente.
        inst = self.institution_name_for_display
        nuc = self.nucleus_display
        team = self.team_display
        
        org_parts = []
        if inst: org_parts.append(f"no {inst}")
        if nuc: org_parts.append(f"no {nuc}")
        if team: org_parts.append(f"na {team}")
        
        # Concatena com vírgulas em vez de barras.
        org_text = ", ".join(org_parts)

        # 5. Tratamento de Gênero
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

        # 6. Montagem Final da Redação
        return (
            f"{date_text}{city_prefix}{org_text}, em conformidade com o disposto no "
            f"artigo 178 do Decreto-Lei nº 3.689, de 3 de outubro de 1941, "
            f"{d_examiner} {examiner} para proceder ao exame pericial, "
            f"em atendimento à requisição expedida {d_authority} {authority}."
        )

    @property
    def report_closing(self):
        return (
            "Esse laudo foi assinado digitalmente e encontra-se arquivado no sistema GDL da "
            "Superintendência da Polícia Técnico-Científica do Estado de São Paulo."
        )


    @property
    def report_signature_block(self) -> dict:
        """
        Bloco de assinatura do perito ao final do laudo.
        """
        name = self.report_identity_name

        role = self._gendered_roles_from_name(
            name=name,
            masculine="Perito Criminal",
            feminine="Perita Criminal",
            neutral="Perito Criminal",
        )

        return {
            "name": name,
            "role": role,
        }
