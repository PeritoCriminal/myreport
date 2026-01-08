from django.urls import path

from report_maker.views.report_case import (
    ReportCaseListView,
    ReportCaseCreateView,
    ReportCaseDetailView,
    ReportCaseUpdateView,
    ReportCaseDeleteView,
)

from report_maker.views.generic_object import (
    GenericExamObjectCreateView,
    GenericExamObjectUpdateView,
    GenericExamObjectDeleteView,
    GenericExamObjectDetailView,
    generic_object_reorder,
)

from report_maker.views.images import (
    ObjectImageCreateView,
    ObjectImageUpdateView,
    ObjectImageDeleteView,
)

app_name = "report_maker"

urlpatterns = [
    # ─────────────────────────────────────
    # Laudos
    # ─────────────────────────────────────
    path("reports/", ReportCaseListView.as_view(), name="report_list"),
    path("reports/create/", ReportCaseCreateView.as_view(), name="report_create"),
    path("reports/<uuid:pk>/", ReportCaseDetailView.as_view(), name="report_detail"),
    path("reports/<uuid:pk>/edit/", ReportCaseUpdateView.as_view(), name="report_update"),
    path("reports/<uuid:pk>/delete/", ReportCaseDeleteView.as_view(), name="report_delete"),

    # ─────────────────────────────────────
    # Objetos de exame (genérico)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:pk>/objects/generic/create/",
        GenericExamObjectCreateView.as_view(),
        name="generic_object_create",
    ),
    path(
        "reports/<uuid:pk>/objects/reorder/",
        generic_object_reorder,
        name="generic_object_reorder",
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
    # (o laudo é inferido via object.report_case)
    # ─────────────────────────────────────
    path(
        "images/<str:app_label>/<str:model>/<uuid:object_id>/add/",
        ObjectImageCreateView.as_view(),
        name="image_add",
    ),
    path(
        "images/<uuid:pk>/edit/",
        ObjectImageUpdateView.as_view(),
        name="image_update",
    ),
    path(
        "images/<uuid:pk>/delete/",
        ObjectImageDeleteView.as_view(),
        name="image_delete",
    ),
]
