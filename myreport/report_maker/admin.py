# report_maker/admin.py
from django.contrib import admin

from .models import ReportCase


@admin.register(ReportCase)
class ReportCaseAdmin(admin.ModelAdmin):
    """
    Admin configuration for ReportCase.

    Goals:
    - Make organizational snapshot explicit (display fields).
    - Prevent accidental edits after the organization has been frozen.
    """

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------
    list_display = (
        "report_number",
        "objective",
        "status",
        "author",
        "institution_display",
        "nucleus_display",
        "team_display",
        "organization_frozen_at",
        "updated_at",
    )
    list_filter = (
        "status",
        "objective",
        "organization_frozen_at",
        "institution",
    )
    search_fields = (
        "report_number",
        "protocol",
        "requesting_authority",
        "author__username",
        "author__display_name",
        "institution__acronym",
        "institution__name",
        "nucleus__name",
        "team__name",
        "institution_acronym_snapshot",
        "institution_name_snapshot",
        "nucleus_name_snapshot",
        "team_name_snapshot",
    )
    ordering = ("-updated_at",)

    autocomplete_fields = ("author", "institution", "nucleus", "team")

    # ------------------------------------------------------------------
    # Readonly defaults
    # ------------------------------------------------------------------
    readonly_fields = (
        "created_at",
        "updated_at",
        "concluded_at",
        "organization_frozen_at",
        "institution_display",
        "nucleus_display",
        "team_display",
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fieldsets = (
        (
            "Identification",
            {
                "fields": (
                    "report_number",
                    "protocol",
                    "author",
                    "objective",
                    "status",
                    "is_locked",
                )
            },
        ),
        (
            "Organization (FK)",
            {
                "fields": (
                    "institution",
                    "nucleus",
                    "team",
                )
            },
        ),
        (
            "Organization (Snapshot)",
            {
                "fields": (
                    "institution_display",
                    "nucleus_display",
                    "team_display",
                    "institution_acronym_snapshot",
                    "institution_name_snapshot",
                    "nucleus_name_snapshot",
                    "team_name_snapshot",
                    "organization_frozen_at",
                )
            },
        ),
        (
            "Request / Occurrence",
            {
                "fields": (
                    "requesting_authority",
                    "police_report",
                    "police_inquiry",
                    "police_station",
                    "occurrence_datetime",
                    "assignment_datetime",
                    "examination_datetime",
                )
            },
        ),
        (
            "Production",
            {
                "fields": (
                    "photography_by",
                    "sketch_by",
                    "conclusion",
                    "pdf_file",
                    "concluded_at",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    # ------------------------------------------------------------------
    # Dynamic readonly behavior
    # ------------------------------------------------------------------
    def get_readonly_fields(self, request, obj=None):
        """
        If organization is frozen, protect both:
        - FK fields (institution/nucleus/team)
        - snapshot fields (so nobody rewrites history manually)
        """
        ro = list(super().get_readonly_fields(request, obj))

        if obj and obj.organization_frozen_at:
            ro.extend(
                [
                    "institution",
                    "nucleus",
                    "team",
                    "institution_acronym_snapshot",
                    "institution_name_snapshot",
                    "nucleus_name_snapshot",
                    "team_name_snapshot",
                ]
            )

        return tuple(ro)
