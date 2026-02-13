# accounts/models.py
from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


def user_profile_image_path(instance: "User", filename: str) -> str:
    """Caminho de upload da imagem de perfil do usuário."""
    return f"{instance.id}/profile/{filename}"


def user_background_image_path(instance: "User", filename: str) -> str:
    """Caminho de upload da imagem de fundo do usuário."""
    return f"{instance.id}/background/{filename}"


def default_can_create_reports_until() -> timezone.datetime.date:
    """
    Data padrão de validade para criação de laudos.

    Atenção: deve ser um callable (função), para evitar que a data fique “congelada”
    no momento do makemigrations. A regra definida aqui concede 90 dias a partir de hoje.
    """
    return timezone.now().date() + timedelta(days=90)


# ─────────────────────────────────────
# Usuário
# ─────────────────────────────────────
class User(AbstractUser):
    """
    Usuário do sistema MyReport (estendido de AbstractUser).

    Permissões de laudos (Report Maker):
    - can_create_reports / can_create_reports_until: controlam a CRIAÇÃO de novos laudos.
    - can_edit_reports: controla a EDIÇÃO de laudos já existentes.
    - As permissões “effective” exigem vínculo institucional ativo.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único (UUID) do usuário.",
    )

    # ─────────────────────────────────────
    # Perfil / Identidade
    # ─────────────────────────────────────
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nome exibido na interface (fallback para username se vazio).",
    )

    report_signature_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nome exibido no bloco de assinatura dos laudos (ex.: Dr. Marcos Capristo).",
    )

    ROLE_PERITO = "PERITO"
    ROLE_DELEGADO = "DELEGADO"
    ROLE_ESCRIVAO = "ESCRIVAO"
    ROLE_FOTOGRAFO = "FOTOGRAFO"

    ROLE_CHOICES = (
        (ROLE_PERITO, "Perito Criminal"),
        (ROLE_DELEGADO, "Delegado de Polícia"),
        (ROLE_ESCRIVAO, "Escrivão"),
        (ROLE_FOTOGRAFO, "Fotógrafo Técnico Pericial"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        help_text="Função do usuário no sistema.",
    )

    # ─────────────────────────────────────
    # Preferências (UI/UX)
    # ─────────────────────────────────────
    THEME_DARK = "dark"
    THEME_LIGHT = "light"
    THEME_SYSTEM = "system"

    THEME_CHOICES = (
        (THEME_DARK, "Escuro"),
        (THEME_LIGHT, "Claro"),
        (THEME_SYSTEM, "Sistema"),
    )

    HOME_DASHBOARD = "dashboard"
    HOME_POSTS = "posts"
    HOME_GROUPS = "groups"
    HOME_TECHNICAL = "technical"
    HOME_REPORTS = "reports"
    HOME_ZEN = "zen"

    HOME_CHOICES = (
        (HOME_DASHBOARD, "Dashboard"),
        (HOME_POSTS, "Postagens"),
        (HOME_GROUPS, "Grupos"),
        (HOME_TECHNICAL, "Arquivo técnico"),
        (HOME_REPORTS, "Laudos"),
        (HOME_ZEN, "Zen do Laudo"),
    )

    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default=THEME_DARK,
        help_text="Tema de interface preferido.",
    )

    default_home = models.CharField(
        max_length=20,
        choices=HOME_CHOICES,
        default=HOME_DASHBOARD,
        help_text="Página inicial padrão ao entrar no sistema.",
    )

    closing_phrase = models.TextField(
        "Frase de Fechamento",
        blank=True,
        default="Nada mais havendo a consignar, encerra-se o presente laudo."
    )

    # ─────────────────────────────────────
    # Imagens
    # ─────────────────────────────────────
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        blank=True,
        null=True,
        help_text="Imagem de perfil do usuário.",
    )

    background_image = models.ImageField(
        upload_to=user_background_image_path,
        blank=True,
        null=True,
        help_text="Imagem de fundo do usuário (faixa superior).",
    )

    # ─────────────────────────────────────
    # Permissões / Flags (Laudos)
    # ─────────────────────────────────────
    can_create_reports = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Habilita o usuário a criar novos laudos (exige vínculo institucional ativo).",
    )

    can_create_reports_until = models.DateField(
        default=default_can_create_reports_until,
        null=True,
        blank=True,
        db_index=True,
        help_text=(
            "Data limite para criação de laudos. "
            "Se vazio (NULL), a criação permanece habilitada sem expiração (desde que can_create_reports=True). "
            "Padrão: 90 dias a partir da data de criação do registro."
        ),
    )

    can_edit_reports = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Habilita o usuário a editar laudos já existentes (exige vínculo institucional ativo).",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        """Representação textual do usuário para admin/logs."""
        return self.display_name or self.username

    def clean(self) -> None:
        """
        Garante que `default_home` armazene somente as chaves suportadas (HOME_*).

        Isso evita salvar valores inválidos via admin/shell/código.
        """
        super().clean()
        allowed_keys = {k for k, _ in self.HOME_CHOICES}
        if self.default_home and self.default_home not in allowed_keys:
            raise ValidationError({"default_home": "Página inicial inválida."})

    # ─────────────────────────────────────
    # Vínculos (atribuições ativas)
    # ─────────────────────────────────────
    @property
    def active_institution_assignment(self):
        """
        Retorna a atribuição institucional ativa mais recente (ou None).

        Requer que exista um related_name `institution_assignments` no model de vínculo.
        """
        return (
            self.institution_assignments.filter(end_at__isnull=True)
            .select_related("institution")
            .order_by("-start_at")
            .first()
        )

    @property
    def active_team_assignment(self):
        """
        Retorna a atribuição de equipe ativa mais recente (ou None).

        Requer que exista um related_name `team_assignments` no model de vínculo.
        """
        return (
            self.team_assignments.filter(end_at__isnull=True)
            .select_related("team")
            .order_by("-start_at")
            .first()
        )

    # ─────────────────────────────────────
    # Permissões efetivas (com vínculo ativo)
    # ─────────────────────────────────────
    @property
    def can_edit_reports_effective(self) -> bool:
        """
        Indica se o usuário pode EDITAR laudos.

        Regra:
        - can_edit_reports precisa estar True;
        - precisa haver vínculo institucional ativo.
        """
        return bool(self.can_edit_reports and self.active_institution_assignment)

    @property
    def can_create_reports_effective(self) -> bool:
        """
        Indica se o usuário pode CRIAR novos laudos.

        Regra:
        - can_create_reports precisa estar True;
        - precisa haver vínculo institucional ativo;
        - se can_create_reports_until estiver preenchido, a data atual deve ser <= limite;
        - se can_create_reports_until for NULL, considera-se sem expiração.
        """
        if not self.can_create_reports:
            return False

        if not self.active_institution_assignment:
            return False

        if self.can_create_reports_until is None:
            return True

        return timezone.now().date() <= self.can_create_reports_until


# ─────────────────────────────────────
# Seguidores
# ─────────────────────────────────────
class UserFollow(models.Model):
    """
    Relação N:N auto-referenciada:
    - follower -> segue -> following

    Observação:
    - is_active permite “desativar” o vínculo sem apagar histórico.
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
        db_index=True,
        help_text="Usuário que segue.",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
        db_index=True,
        help_text="Usuário seguido.",
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Data/hora de criação do vínculo (follow).",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica se o vínculo está ativo.",
    )

    class Meta:
        db_table = "accounts_user_follow"
        verbose_name = "Seguir usuário"
        verbose_name_plural = "Seguidores e seguidos"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="uniq_user_follow_pair",
            ),
            models.CheckConstraint(
                check=~Q(follower=models.F("following")),
                name="chk_no_self_follow",
            ),
        ]
        indexes = [
            models.Index(fields=["follower", "is_active"]),
            models.Index(fields=["following", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Representação textual do follow para admin/logs."""
        status = "active" if self.is_active else "inactive"
        return f"{self.follower} -> {self.following} ({status})"
