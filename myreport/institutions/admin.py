# institutions/admin.py
from django.contrib import admin

from .models import (
    Institution,
    InstitutionCity,
    Nucleus,
    Team
)


# ---------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------
class InstitutionCityInline(admin.TabularInline):
    model = InstitutionCity
    extra = 0
    fields = ("order", "name", "state", "is_active") # aqui precisamos incluir "honoree"
    ordering = ("order", "name")


class NucleusInline(admin.TabularInline):
    model = Nucleus
    extra = 0
    fields = ("order", "name", "city", "is_active")
    ordering = ("order", "name")
    autocomplete_fields = ("city",)


class TeamInline(admin.TabularInline):
    model = Team
    extra = 0
    fields = ("order", "name", "description", "is_active")
    ordering = ("order", "name")


# ---------------------------------------------------------------------
# Institution
# ---------------------------------------------------------------------
@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = (
        "acronym",
        "name",
        "kind",
        "director_name",
        "is_active",
        "updated_at",
    )
    list_filter = ("kind", "is_active")
    search_fields = ("acronym", "name", "director_name", "director_title")
    ordering = ("acronym",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Identification", {"fields": ("acronym", "name", "kind", "is_active")}),
        ("Homenagem institucional", {"fields": ("honoree_title", "honoree_name")}),
        ("Direction", {"fields": ("director_name", "director_title")}),
        ("Emblems", {"fields": ("emblem_primary", "emblem_secondary")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    inlines = (InstitutionCityInline, NucleusInline)


# ---------------------------------------------------------------------
# InstitutionCity
# ---------------------------------------------------------------------
@admin.register(InstitutionCity)
class InstitutionCityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "institution", "order", "is_active")
    list_filter = ("state", "is_active", "institution")
    search_fields = ("name", "institution__acronym", "institution__name")
    ordering = ("institution__acronym", "order", "name")
    autocomplete_fields = ("institution",)


# ---------------------------------------------------------------------
# Nucleus
# ---------------------------------------------------------------------
@admin.register(Nucleus)
class NucleusAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "city", "order", "is_active")
    list_filter = ("is_active", "institution", "city__state")
    search_fields = (
        "name",
        "institution__acronym",
        "institution__name",
        "city__name",
    )
    ordering = ("institution__acronym", "order", "name")
    autocomplete_fields = ("institution", "city")

    inlines = (TeamInline,)


# ---------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "nucleus",
        "institution_acronym",
        "order",
        "is_active",
    )
    list_filter = ("is_active", "nucleus__institution")
    search_fields = (
        "name",
        "description",
        "nucleus__name",
        "nucleus__institution__acronym",
    )
    ordering = (
        "nucleus__institution__acronym",
        "nucleus__order",
        "order",
        "name",
    )
    autocomplete_fields = ("nucleus",)

    @admin.display(
        description="Institution",
        ordering="nucleus__institution__acronym",
    )
    def institution_acronym(self, obj):
        return obj.nucleus.institution.acronym
