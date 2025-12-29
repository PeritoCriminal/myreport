# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Greatest, Least
from django.utils import timezone
import uuid



def user_profile_image_path(instance, filename):
    return f"{instance.id}/profile/{filename}"


def user_background_image_path(instance, filename):
    return f"{instance.id}/background/{filename}"


class User(AbstractUser):
    """
    Modelo de usuário estendido para o sistema EPCL.
    Baseado em AbstractUser.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Nome exibido no sistema
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nome exibido na interface."
    )

    # Papéis possíveis
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

    # Papel do usuário no sistema
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        help_text="Função do usuário no sistema."
    )

    # Imagem de perfil (quadrada)
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        blank=True,
        null=True
    )

    # Imagem de fundo (retangular)
    background_image = models.ImageField(
        upload_to=user_background_image_path,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.display_name or self.username



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
    is_active = models.BooleanField(default=True, db_index=True)  # segue seu padrão de "desativar"

    class Meta:
        db_table = "accounts_user_follow"
        verbose_name = "Seguir usuário"
        verbose_name_plural = "Seguidores e seguidos"

        constraints = [
            # impede duplicidade (mesmo follower -> following)
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="uniq_user_follow_pair",
            ),
            # impede auto-seguir
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
        return f"{self.follower} -> {self.following} ({'active' if self.is_active else 'inactive'})"
