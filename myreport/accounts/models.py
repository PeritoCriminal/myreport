# accounts/models.py
from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


def user_profile_image_path(instance: "User", filename: str) -> str:
    return f"{instance.id}/profile/{filename}"


def user_background_image_path(instance: "User", filename: str) -> str:
    return f"{instance.id}/background/{filename}"


# --------------------------------------------------
# Usuário
# --------------------------------------------------
class User(AbstractUser):
    """
    Usuário do sistema EPCL, estendido a partir de AbstractUser.

    A autorização para editar laudos é controlada por sinal administrativo
    e por vínculo institucional ativo.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ─────────────────────────────────────
    # Perfil / Identidade
    # ─────────────────────────────────────
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nome exibido na interface.",
    )

    report_signature_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nome exibido nos Laudos. Ex: Dr. Marcos Capristo",
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
    )

    default_home = models.CharField(
        max_length=20,
        choices=HOME_CHOICES,
        default=HOME_DASHBOARD,
    )

    # ─────────────────────────────────────
    # Imagens
    # ─────────────────────────────────────
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        blank=True,
        null=True,
    )

    background_image = models.ImageField(
        upload_to=user_background_image_path,
        blank=True,
        null=True,
    )

    # ─────────────────────────────────────
    # Permissões / Flags
    # ─────────────────────────────────────
    can_edit_reports = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Habilita o usuário a criar/editar laudos (exige vínculo institucional ativo).",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.display_name or self.username

    def clean(self):
        """
        Garante que `default_home` armazene somente as CHAVES suportadas (HOME_*).
        Isso evita salvar valores como 'document_list' via admin/shell/código.
        """
        super().clean()
        allowed_keys = {k for k, _ in self.HOME_CHOICES}
        if self.default_home and self.default_home not in allowed_keys:
            raise ValidationError({"default_home": "Página inicial inválida."})

    @property
    def active_institution_assignment(self):
        return (
            self.institution_assignments.filter(end_at__isnull=True)
            .select_related("institution")
            .order_by("-start_at")
            .first()
        )

    @property
    def active_team_assignment(self):
        return (
            self.team_assignments.filter(end_at__isnull=True)
            .select_related("team")
            .order_by("-start_at")
            .first()
        )

    @property
    def can_edit_reports_effective(self) -> bool:
        return bool(self.can_edit_reports and self.active_institution_assignment)


# --------------------------------------------------
# Seguidores
# --------------------------------------------------
class UserFollow(models.Model):
    """
    Relação N:N auto-referenciada:
    follower -> segue -> following
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
        db_index=True,
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
        db_index=True,
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

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
        status = "active" if self.is_active else "inactive"
        return f"{self.follower} -> {self.following} ({status})"
