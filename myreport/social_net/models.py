# social_net/models.py
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_save 
from django.dispatch import receiver         
from django.utils import timezone

from PIL import Image, ImageOps


# =========================
# Paths
# =========================
def post_media_path(instance, filename: str) -> str:
    """
    Retorna o caminho de armazenamento do arquivo de mídia associado a uma postagem.
    """
    ext = os.path.splitext(filename)[1].lower()
    return f"{instance.user_id}/posts/{instance.id}/{uuid.uuid4()}{ext}"


def comment_image_path(instance, filename: str) -> str:
    """
    Retorna o caminho de armazenamento da imagem associada a um comentário.
    """
    ext = os.path.splitext(filename)[1].lower()
    return f"{instance.post_id}/comments/{instance.id}/{uuid.uuid4()}{ext}"


# =========================
# Image optimization helper
# =========================
def _optimize_image_field(
    instance,
    field_name: str,
    *,
    max_side: int = 1920,
    quality: int = 85,
) -> bool:
    """
    Otimiza uma imagem (se o arquivo for imagem legível pelo Pillow):
    - corrige orientação EXIF;
    - converte para RGB;
    - redimensiona mantendo proporção (sem aumentar);
    - regrava como JPEG com compressão;
    Retorna True se otimizou e substituiu o arquivo, senão False.
    """
    f = getattr(instance, field_name, None)
    if not f:
        return False

    try:
        f.open("rb")
        img = Image.open(f)
        img.load()
    except Exception:
        # Não é imagem (ou não legível) => não mexe
        return False
    finally:
        try:
            f.close()
        except Exception:
            pass

    # Processamento e otimização da imagem
    img = ImageOps.exif_transpose(img)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Redimensionamento
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    # Cria buffer de saída
    out = BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    out.seek(0)

    # Gera novo nome (mantendo o caminho, mas garantindo extensão .jpg)
    old_name = f.name or ""
    dir_name = os.path.dirname(old_name)
    base = os.path.splitext(os.path.basename(old_name))[0] or uuid.uuid4().hex
    new_name = f"{dir_name}/{base}.jpg" if dir_name else f"{base}.jpg"

    # Substitui o arquivo (sem salvar o model ainda - importante para pre_save)
    getattr(instance, field_name).save(new_name, ContentFile(out.read()), save=False)
    return True


# =========================
# Models
# =========================
class Post(models.Model):
    """
    Representa uma postagem criada por um usuário, podendo conter texto e um arquivo de mídia opcional.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    title = models.CharField("Título", max_length=120, blank=True)
    text = models.TextField("Texto", blank=True)

    media = models.FileField(
        "Mídia",
        upload_to=post_media_path,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Limites de imagem (para exibição com qualidade em tela 19")
    IMAGE_MAX_SIDE = 1920
    IMAGE_QUALITY = 85

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        verbose_name = "Postagem"
        verbose_name_plural = "Postagens"

    def __str__(self) -> str:
        return f"{self.title or 'Post'} ({self.user_id})"

    def save(self, *args, **kwargs):
        """
        Salva a postagem. A otimização de imagem foi movida para o signal pre_save.
        """
        # A otimização ocorre no pre_save. Aqui, apenas o salvamento principal.
        super().save(*args, **kwargs)


class PostLike(models.Model):
    """
    Registra a curtida de um usuário em uma postagem, permitindo no máximo uma curtida por usuário/post.
    """

    post = models.ForeignKey(
        "social_net.Post",
        on_delete=models.CASCADE,
        related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Curtida"
        verbose_name_plural = "Curtidas"
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="uniq_post_like"),
        ]

    def __str__(self) -> str:
        return f"Like: {self.post_id} / {self.user_id}"


class PostRating(models.Model):
    """
    Registra a avaliação (1 a 5) de um usuário em uma postagem, permitindo no máximo uma avaliação por usuário/post.
    """

    post = models.ForeignKey(
        "social_net.Post",
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_ratings",
    )
    value = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="uniq_post_rating"),
            models.CheckConstraint(
                check=models.Q(value__gte=1) & models.Q(value__lte=5),
                name="rating_value_1_to_5",
            ),
        ]

    def __str__(self) -> str:
        return f"Rating {self.value}: {self.post_id} / {self.user_id}"


class PostComment(models.Model):
    """
    Representa um comentário em uma postagem, com suporte a resposta encadeada e imagem opcional.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    post = models.ForeignKey(
        "social_net.Post",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_comments",
    )

    text = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=comment_image_path,
        blank=True,
        null=True,
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Limites de imagem (para exibição com qualidade em tela 19")
    IMAGE_MAX_SIDE = 1920
    IMAGE_QUALITY = 85

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(~models.Q(text="")) | models.Q(image__isnull=False),
                name="comment_requires_text_or_image",
            ),
        ]

    def __str__(self) -> str:
        return f"Comment: {self.post_id} / {self.user_id}"

    def save(self, *args, **kwargs):
        """
        Salva o comentário. A otimização e a atualização do updated_at do Post
        foram movidas para os signals pre_save e post_save.
        """
        super().save(*args, **kwargs)


# =========================
# Signals para otimização e updated_at
# =========================

@receiver(pre_save, sender=Post)
def optimize_post_media(sender, instance, **kwargs):
    """
    Otimiza a imagem do Post ANTES de ser salva no storage,
    evitando que o arquivo original (grande) seja salvo primeiro.
    """
    _optimize_image_field(
        instance,
        "media",
        max_side=instance.IMAGE_MAX_SIDE,
        quality=instance.IMAGE_QUALITY,
    )


@receiver(pre_save, sender=PostComment)
def optimize_comment_image(sender, instance, **kwargs):
    """
    Otimiza a imagem do Comentário ANTES de ser salva no storage,
    evitando que o arquivo original (grande) seja salvo primeiro.
    """
    _optimize_image_field(
        instance,
        "image",
        max_side=instance.IMAGE_MAX_SIDE,
        quality=instance.IMAGE_QUALITY,
    )
    
@receiver(models.signals.post_save, sender=PostComment)
def update_post_on_comment_save(sender, instance, created, **kwargs):
    """
    Atualiza o campo 'updated_at' da Postagem para trazê-la para o topo
    sempre que um novo comentário for salvo (criado ou modificado).
    """
    if created or instance.pk is not None:
        # Usa Post.objects.filter().update para evitar carregar o objeto
        # Post e evitar um loop de save recursivo.
        Post.objects.filter(pk=instance.post_id).update(updated_at=timezone.now())