from django.urls import path

from report_maker.views.report_case import (
    ReportCaseListView,
    ReportCaseCreateView,
    ReportCaseDetailView,
    ReportCaseUpdateView,
)

from report_maker.views.generic_object import (
    GenericExamObjectCreateView,
    GenericExamObjectUpdateView,
    GenericExamObjectDeleteView,
    GenericExamObjectDetailView,
)

from report_maker.views.images import (
    ObjectImageCreateView,
    ObjectImageDeleteView,
)

app_name = "report_maker"

urlpatterns = [
    # ─────────────────────────────────────
    # Laudos
    # ─────────────────────────────────────
    path("reports/", ReportCaseListView.as_view(), name="report_list"),
    path("reports/create/", ReportCaseCreateView.as_view(), name="report_create"),
    path("reports/<uuid:pk>/edit/", ReportCaseUpdateView.as_view(), name="report_update"),
    path("reports/<uuid:pk>/", ReportCaseDetailView.as_view(), name="report_detail"),

    # ─────────────────────────────────────
    # Objetos de exame (genérico)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_id>/objects/generic/create/",
        GenericExamObjectCreateView.as_view(),
        name="generic_object_create",
    ),
    path(
        "objects/generic/<uuid:pk>/",
        GenericExamObjectDetailView.as_view(),
        name="generic_object_detail",
    ),
    path(
        "objects/generic/<uuid:pk>/edit/",
        GenericExamObjectUpdateView.as_view(),
        name="generic_object_update",
    ),
    path(
        "objects/generic/<uuid:pk>/delete/",
        GenericExamObjectDeleteView.as_view(),
        name="generic_object_delete",
    ),

    # ─────────────────────────────────────
    # Imagens vinculadas a objetos
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_id>/images/<str:app_label>/<str:model>/<uuid:object_id>/add/",
        ObjectImageCreateView.as_view(),
        name="image_add",
    ),
    path(
        "images/<uuid:pk>/delete/",
        ObjectImageDeleteView.as_view(),
        name="image_delete",
    ),
]
