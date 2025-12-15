# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
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
