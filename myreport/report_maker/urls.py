from django.urls import path

from report_maker.views.report_case import (
    ReportCaseListView,
    ReportCaseCreateView,
    ReportCaseDetailView,
    ReportCaseUpdateView,
    ReportCaseDeleteView,
)

from report_maker.views.report_case_close import ReportCaseCloseView

from report_maker.views.exam_object_dashboard import ExamObjectDashboardView

from report_maker.views.generic_object import (
    GenericExamObjectCreateView,
    GenericExamObjectUpdateView,
    GenericExamObjectDeleteView,
    GenericExamObjectDetailView,
    generic_object_reorder,
)

from report_maker.views.exam_public_road import (
    PublicRoadExamObjectListView,
    PublicRoadExamObjectCreateView,
    PublicRoadExamObjectDetailView,
    PublicRoadExamObjectUpdateView,
    PublicRoadExamObjectDeleteView,
)

from report_maker.views.images import (
    ObjectImageCreateView,
    ObjectImageUpdateView,
    ObjectImageDeleteView,
    images_reorder,
)

from report_maker.views.report_case_preview import (
    ReportCasePreviewView,
)

app_name = "report_maker"

urlpatterns = [
    # ─────────────────────────────────────
    # Laudos
    # ─────────────────────────────────────
    path("reports/", ReportCaseListView.as_view(), name="report_list"),
    path("reports/create/", ReportCaseCreateView.as_view(), name="report_create"),
    path("reports/<uuid:pk>/", ReportCaseDetailView.as_view(), name="report_detail"),
    path("reports/<uuid:pk>/preview/", ReportCasePreviewView.as_view(), name="report_preview"),
    path("reports/<uuid:pk>/edit/", ReportCaseUpdateView.as_view(), name="report_update"),
    path("reports/<uuid:pk>/delete/", ReportCaseDeleteView.as_view(), name="report_delete"),
    path("reports/<uuid:pk>/close/", ReportCaseCloseView.as_view(), name="report_close"),

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
    # Dashboard para objetos de Exame
    # ─────────────────────────────────────
    path(
        "reports/<uuid:pk>/objects/add/",
        ExamObjectDashboardView.as_view(),
        name="exam_object_dashboard",
    ),

    # ─────────────────────────────────────
    # Objetos de exame (Via Pública)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_pk>/objects/public-road/",
        PublicRoadExamObjectListView.as_view(),
        name="public_road_object_list",
    ),
    path(
        "reports/<uuid:report_pk>/objects/public-road/create/",
        PublicRoadExamObjectCreateView.as_view(),
        name="public_road_object_create",
    ),
    path(
        "objects/public-road/<uuid:pk>/",
        PublicRoadExamObjectDetailView.as_view(),
        name="public_road_object_detail",
    ),
    path(
        "objects/public-road/<uuid:pk>/edit/",
        PublicRoadExamObjectUpdateView.as_view(),
        name="public_road_object_update",
    ),
    path(
        "objects/public-road/<uuid:pk>/delete/",
        PublicRoadExamObjectDeleteView.as_view(),
        name="public_road_object_delete",
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
    path("images/reorder/", images_reorder, name="images_reorder"),
]
