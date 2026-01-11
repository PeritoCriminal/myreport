# institutions/admin.py
from django.contrib import admin

from .models import Equipe, Institution, InstitutionCity, Nucleo


class InstitutionCityInline(admin.TabularInline):
    model = InstitutionCity
    extra = 0
    fields = ("order", "name", "state", "is_active")
    ordering = ("order", "name")


class NucleoInline(admin.TabularInline):
    model = Nucleo
    extra = 0
    fields = ("order", "nome", "cidade", "is_active")
    ordering = ("order", "nome")
    autocomplete_fields = ("cidade",)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("sigla", "nome", "kind", "diretor_nome", "is_active", "updated_at")
    list_filter = ("kind", "is_active")
    search_fields = ("sigla", "nome", "diretor_nome", "diretor_cargo")
    ordering = ("sigla",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Identificação", {"fields": ("sigla", "nome", "kind", "is_active")}),
        ("Direção", {"fields": ("diretor_nome", "diretor_cargo")}),
        ("Brasões", {"fields": ("brasao_1", "brasao_2")}),
        ("Auditoria", {"fields": ("created_at", "updated_at")}),
    )

    inlines = (InstitutionCityInline, NucleoInline)


@admin.register(InstitutionCity)
class InstitutionCityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "institution", "order", "is_active")
    list_filter = ("state", "is_active", "institution")
    search_fields = ("name", "institution__sigla", "institution__nome")
    ordering = ("institution__sigla", "order", "name")
    autocomplete_fields = ("institution",)


class EquipeInline(admin.TabularInline):
    model = Equipe
    extra = 0
    fields = ("order", "nome", "descricao", "is_active")
    ordering = ("order", "nome")


@admin.register(Nucleo)
class NucleoAdmin(admin.ModelAdmin):
    list_display = ("nome", "institution", "cidade", "order", "is_active")
    list_filter = ("is_active", "institution", "cidade__state")
    search_fields = ("nome", "institution__sigla", "institution__nome", "cidade__name")
    ordering = ("institution__sigla", "order", "nome")
    autocomplete_fields = ("institution", "cidade")

    inlines = (EquipeInline,)


@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ("nome", "nucleo", "institution_sigla", "order", "is_active")
    list_filter = ("is_active", "nucleo__institution")
    search_fields = ("nome", "descricao", "nucleo__nome", "nucleo__institution__sigla")
    ordering = ("nucleo__institution__sigla", "nucleo__order", "order", "nome")
    autocomplete_fields = ("nucleo",)

    @admin.display(description="Instituição", ordering="nucleo__institution__sigla")
    def institution_sigla(self, obj):
        return obj.nucleo.institution.sigla
