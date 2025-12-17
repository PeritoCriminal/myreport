# social_net/models.py
import uuid
from django.conf import settings
from django.db import models


def post_media_path(instance, filename: str) -> str:
    # ex: <user_uuid>/posts/<post_uuid>/<filename>
    return f"{instance.user_id}/posts/{instance.id}/{filename}"


class Post(models.Model):
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)  # opcional: “soft delete”

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.user_id})"

