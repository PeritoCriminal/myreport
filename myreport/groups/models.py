import uuid

from django.conf import settings
from django.db import models




def group_profile_image_path(instance, filename):
    return f"groups/{instance.id}/profile/{filename}"


def group_background_image_path(instance, filename):
    return f"groups/{instance.id}/background/{filename}"




class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="groups_created",
        verbose_name="Criador",
    )

    name = models.CharField(max_length=120, unique=True, verbose_name="Nome")

    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )

    profile_image = models.ImageField(
        upload_to=group_profile_image_path,
        blank=True,
        null=True,
        verbose_name="Imagem de perfil",
    )

    background_image = models.ImageField(
        upload_to=group_background_image_path,
        blank=True,
        null=True,
        verbose_name="Imagem de fundo",
    )

    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name




class GroupMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Grupo",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
        verbose_name="Usuário",
    )

    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Entrou em")

    class Meta:
        verbose_name = "Membro do grupo"
        verbose_name_plural = "Membros do grupo"
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_group_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.group}"
