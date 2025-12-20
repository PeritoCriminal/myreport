# social_net/admin.py
from django.contrib import admin

from .models import Post, PostComment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at", "user")
    search_fields = ("id", "title", "text", "user__username", "user__email")
    ordering = ("-updated_at",)
    date_hierarchy = "created_at"
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "is_active", "created_at", "parent")
    list_filter = ("is_active", "created_at", "user")
    search_fields = ("id", "text", "user__username", "user__email", "post__id")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    raw_id_fields = ("post", "user", "parent")
    readonly_fields = ("created_at",)
