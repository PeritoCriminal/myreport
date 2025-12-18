# social_net/models.py
import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


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
    return f"{instance.post_id}/comments/{instance.id}{ext}"


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

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        verbose_name = "Postagem"
        verbose_name_plural = "Postagens"

    def __str__(self) -> str:
        return f"{self.title or 'Post'} ({self.user_id})"


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
        Salva o comentário e atualiza o campo `updated_at` da postagem associada.

        Mantém o comportamento de `auto_now` do Post coerente com interações
        relevantes (comentários) sem depender de signals.
        """
        super().save(*args, **kwargs)

        Post.objects.filter(pk=self.post_id).update(updated_at=timezone.now())

