from django.contrib import admin
from .models import (
    TechnicalTopic,
    TechnicalDocument,
    TechnicalDocumentVersion,
)


@admin.register(TechnicalTopic)
class TechnicalTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


class TechnicalDocumentVersionInline(admin.TabularInline):
    model = TechnicalDocumentVersion
    extra = 0
    fields = (
        "version",
        "pdf_file",
        "is_current",
        "created_by",
        "created_at",
        "notes",
    )
    readonly_fields = ("created_at",)
    ordering = ("-version",)

    # evita apagar versão pelo admin (histórico)
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TechnicalDocument)
class TechnicalDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "topic",
        "created_by",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "topic")
    search_fields = ("title", "description", "topic__name", "created_by__username")
    ordering = ("-updated_at",)
    autocomplete_fields = ("topic", "created_by")
    inlines = (TechnicalDocumentVersionInline,)

    # protege contra deleção pelo admin (segue seu padrão de inativar)
    def has_delete_permission(self, request, obj=None):
        return False

    actions = ("deactivate_selected", "activate_selected")

    @admin.action(description="Inativar documentos selecionados")
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Ativar documentos selecionados")
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)


@admin.register(TechnicalDocumentVersion)
class TechnicalDocumentVersionAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "version",
        "is_current",
        "created_by",
        "created_at",
    )
    list_filter = ("is_current", "document__topic")
    search_fields = ("document__title", "document__topic__name", "created_by__username")
    ordering = ("-created_at",)
    autocomplete_fields = ("document", "created_by")
    readonly_fields = ("created_at",)

    # evita apagar versões direto pelo admin
    def has_delete_permission(self, request, obj=None):
        return False
