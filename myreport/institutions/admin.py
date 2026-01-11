# institutions/admin.py

from django.contrib import admin

from .models import (
    FederationUnit,
    Institution,
    ForensicAgency,
    WorkUnit,
    InstitutionalProfile,
)


@admin.register(FederationUnit)
class FederationUnitAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "uf")
    list_filter = ("uf",)
    search_fields = ("name", "short_name", "uf__code", "uf__name")
    autocomplete_fields = ("uf",)
    ordering = ("uf__code", "name")


@admin.register(ForensicAgency)
class ForensicAgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "institution", "uf_code", "superintendent_name")
    list_filter = ("institution__uf", "institution")
    search_fields = (
        "name",
        "city",
        "superintendent_name",
        "institution__name",
        "institution__short_name",
        "institution__uf__code",
        "institution__uf__name",
    )
    autocomplete_fields = ("institution",)
    ordering = ("institution__uf__code", "name", "city")

    @admin.display(description="UF", ordering="institution__uf__code")
    def uf_code(self, obj):
        return obj.institution.uf.code


@admin.register(WorkUnit)
class WorkUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "agency", "institution", "uf_code")
    list_filter = ("agency__institution__uf", "agency__institution", "agency")
    search_fields = (
        "name",
        "city",
        "agency__name",
        "agency__city",
        "agency__institution__name",
        "agency__institution__short_name",
        "agency__institution__uf__code",
        "agency__institution__uf__name",
    )
    autocomplete_fields = ("agency",)
    ordering = ("agency__institution__uf__code", "agency__name", "name")

    @admin.display(description="Instituição", ordering="agency__institution__name")
    def institution(self, obj):
        return obj.agency.institution

    @admin.display(description="UF", ordering="agency__institution__uf__code")
    def uf_code(self, obj):
        return obj.agency.institution.uf.code


@admin.register(InstitutionalProfile)
class InstitutionalProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "work_unit", "examiner_display_name", "is_active", "uf_code")
    list_filter = ("is_active", "work_unit__agency__institution__uf", "work_unit__agency")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "examiner_display_name",
        "work_unit__name",
        "work_unit__agency__name",
        "work_unit__agency__institution__name",
        "work_unit__agency__institution__short_name",
        "work_unit__agency__institution__uf__code",
    )
    autocomplete_fields = ("user", "work_unit")
    ordering = ("user__username",)

    @admin.display(description="UF", ordering="work_unit__agency__institution__uf__code")
    def uf_code(self, obj):
        if obj.work_unit_id:
            return obj.work_unit.agency.institution.uf.code
        return ""
