# report_maker/models/exam_base.py

from __future__ import annotations

import uuid
from typing import TypedDict, Literal, ClassVar

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _


class ExamObjectGroup(models.TextChoices):
    LOCATIONS = "LOCATIONS", _("Locais")
    VEHICLES = "VEHICLES", _("Veículos")
    PARTS = "PARTS", _("Peças")
    CADAVERS = "CADAVERS", _("Cadáveres")
    OTHER = "OTHER", _("Outros")


# ─────────────────────────────────────────────────────────────
# Contrato de renderização (sem numeração)
# ─────────────────────────────────────────────────────────────

class RenderBlock(TypedDict, total=False):
    """
    Um bloco de renderização "relativo" ao título do objeto.
    A view decide o nível absoluto (T1/T2/T3...) e numeração.

    kind="section_field":
        - label: vira um título abaixo do title do objeto
        - field: conteúdo vira texto normal

    kind="render_section":
        - key: chave para ser renderizada pelo RenderableExamObjectMixin (ex.: 'exam', 'results')
        - label: título abaixo do title
        - fmt: "md" ou "text" (a view decide como converter)
    """
    kind: Literal["section_field", "render_section"]
    label: str
    field: str
    key: str
    fmt: Literal["text", "md"]


class ExamObject(models.Model):
    """
    Base comum para todos os objetos examinados em um laudo.

    - group_key: persiste no BD e serve para agrupamento no laudo
    - GROUP_KEY: constante por classe concreta para travar consistência
        * None/"": significa "sem grupo" (objeto vira T1 direto)
    - get_render_blocks(): descreve a estrutura do objeto sem numeração
    """

    GROUP_KEY: ClassVar[str | None] = ExamObjectGroup.OTHER  # sobrescreva nos filhos (pode ser None)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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
        null=True,
        help_text="Ordem de exibição do objeto dentro do laudo.",
    )

    group_key = models.CharField(
        "Grupo",
        max_length=24,
        choices=ExamObjectGroup.choices,
        blank=True,
        null=True,
        db_index=True,
        editable=False,
        help_text="Agrupamento lógico no laudo (Locais, Veículos, Peças, Cadáveres...). Vazio = sem grupo.",
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

    def _is_filled(self, value) -> bool:
        """
        Considera preenchido quando há conteúdo útil.
        Se vier HTML, strip_tags evita contar '<p><br></p>' como texto.
        """
        if value is None:
            return False
        if not isinstance(value, str):
            return bool(value)
        text = strip_tags(value).strip()
        return bool(text)

    def get_render_sections(self):
        """
        Se o objeto concreto/mixin definir RENDER_SECTIONS, usa.
        Caso contrário, fica no padrão: somente description.
        Estrutura esperada: [(field_name, label), ...]
        """
        sections = getattr(self, "RENDER_SECTIONS", None)
        if sections:
            return sections
        return [("description", "Descrição")]

    def get_render_blocks(self):
        """
        Regra global:
        - Se só 1 campo renderizável estiver preenchido, não renderiza label de seção.
        - Se 2+ estiverem preenchidos, renderiza labels normalmente.
        """
        sections = self.get_render_sections()

        filled = []
        for field_name, label in sections:
            value = getattr(self, field_name, None)
            if self._is_filled(value):
                filled.append((field_name, label, value))

        if not filled:
            return []

        # Apenas um campo preenchido => bloco inline (sem subtítulo)
        if len(filled) == 1:
            field_name, _label, _value = filled[0]
            return [{
                "kind": "section_field",
                "field_name": field_name,
                "label": "",          # ou None
                "inline": True,       # <- sinal para template/view
            }]

        # Dois ou mais => seções normais
        blocks = []
        for field_name, label, _value in filled:
            blocks.append({
                "kind": "section_field",
                "field_name": field_name,
                "label": label,
                "inline": False,
            })
        return blocks


    def save(self, *args, **kwargs):
        # trava consistência do grupo com base na classe concreta
        group_key = getattr(self, "GROUP_KEY", None)

        if isinstance(group_key, str):
            group_key = group_key.strip()

        # None/"": significa "sem grupo" (objeto vira T1 direto)
        self.group_key = group_key or None

        if self.order is None:
            last = (
                ExamObject.objects
                .filter(report_case=self.report_case)
                .aggregate(last_order=Max("order"))
                .get("last_order")
            )
            self.order = (last or 0) + 1

        super().save(*args, **kwargs)

    # ─────────────────────────────────────
    # Renderização (estrutura relativa)
    # ─────────────────────────────────────

    @classmethod
    def get_object_title_field(cls) -> str:
        """
        Campo que representa o TÍTULO do objeto (nível base do objeto).
        A view decide se isso vira 4.1 ou 4.1.1, etc.
        """
        return "title"

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        """
        Blocos do objeto (SEÇÕES) abaixo do título do objeto.
        Cada bloco tem um rótulo (título abaixo) e um conteúdo (texto normal).

        No base: "Descrição" -> description
        """
        return [
            {
                "kind": "section_field",
                "label": "Descrição",
                "field": "description",
                "fmt": "text",
            }
        ]

    @property
    def group_label(self) -> str:
        if not self.group_key:
            return ""
        try:
            return ExamObjectGroup(self.group_key).label
        except ValueError:
            return str(self.group_key)

    # ─────────────────────────────────────
    # Downcast utilitário (mantém seu fluxo atual)
    # ─────────────────────────────────────

    @property
    def concrete(self):
        """
        Retorna a instância concreta (filha) quando existir.
        Útil para preview/templates (downcast manual).
        """
        for rel in (
            "publicroadexamobject",
            "vehicleinspectionexamobject",
            "genericexamobject",
            "genericlocationexamobject",
            "cadaverexamobject",
            # "novos_elementos",  # incluir quando criar novos models.
        ):
            if hasattr(self, rel):
                return getattr(self, rel)
        return self

    @property
    def edit_url(self):
        c = self.concrete
        url_name = getattr(c, "edit_url_name", None)
        if not url_name:
            return None
        return reverse(url_name, args=[self.report_case_id, c.pk])

    @property
    def delete_url(self):
        c = self.concrete
        url_name = getattr(c, "delete_url_name", None)
        if not url_name:
            return None
        return reverse(url_name, args=[self.report_case_id, c.pk])

    @property
    def app_label(self) -> str:
        return self._meta.app_label

    @property
    def model_name(self) -> str:
        return self._meta.model_name

    # opcional (se em algum lugar você usa "model" no template)
    @property
    def model(self) -> str:
        return self._meta.model_name

    @property
    def concrete_app_label(self) -> str:
        return self.concrete._meta.app_label

    @property
    def concrete_model_name(self) -> str:
        return self.concrete._meta.model_name

    def __str__(self) -> str:
        return self.title or f"Objeto ({self.pk})"
