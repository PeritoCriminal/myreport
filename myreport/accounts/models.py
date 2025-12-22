# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
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




class Friendship(models.Model):
    """
    Representa a relação de amizade entre dois usuários do sistema.

    O modelo registra uma solicitação de amizade iniciada por `from_user`
    (solicitante) em direção a `to_user` (destinatário), mantendo o estado
    da relação por meio do campo `status`.

    Estados possíveis:
    - P (PENDING): solicitação enviada e ainda não respondida;
    - A (ACCEPTED): solicitação aceita, estabelecendo a amizade;
    - D (DECLINED): solicitação recusada;
    - B (BLOCKED): relação bloqueada, conforme regras da aplicação.

    Regras de integridade:
    - Não é permitida amizade de um usuário consigo mesmo.
    - É permitida apenas uma única relação por par de usuários,
      independentemente da direção (A-B ou B-A). Assim, se existir
      uma solicitação A→B, não é possível criar B→A.
    - Tentativas de criação de uma relação inversa devem ser tratadas
      pela aplicação, informando ao usuário a existência de solicitação
      pendente ou relação já estabelecida.

    Campos de auditoria:
    - `created_at`: data e hora da criação da solicitação.
    - `responded_at`: data e hora da resposta à solicitação, quando aplicável.

    Observação:
    - A unicidade não direcional do par é garantida no nível do banco de dados
      por meio de constraint, prevenindo duplicidade mesmo em cenários de
      concorrência.
    """
    class Status(models.TextChoices):
        PENDING = "P", "Pendente"
        ACCEPTED = "A", "Aceita"
        DECLINED = "D", "Recusada"
        BLOCKED = "B", "Bloqueada"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_received",
    )

    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # impede self
            models.CheckConstraint(
                check=~models.Q(from_user=models.F("to_user")),
                name="no_self_friendship",
            ),

            # impede A->B e B->A simultaneamente (unicidade por par não-direcional)
            models.UniqueConstraint(
                Least("from_user_id", "to_user_id"),
                Greatest("from_user_id", "to_user_id"),
                name="uniq_friendship_undirected_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["from_user", "status"]),
            models.Index(fields=["to_user", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.from_user} -> {self.to_user} ({self.get_status_display()})"
