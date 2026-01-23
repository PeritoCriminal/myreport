# report_maker/urls.py
from django.urls import path

from report_maker.views.report_case import (
    ReportCaseListView,
    ReportCaseCreateView,
    ReportCaseDetailView,
    ReportCaseUpdateView,
    ReportCaseDeleteView,
)

from report_maker.views.report_case_close import ReportCaseCloseView
from report_maker.views.report_case_preview import ReportCasePreviewView

from report_maker.views.exam_object_dashboard import ExamObjectDashboardView
from report_maker.views.exam_objects_reorder import exam_objects_reorder

from report_maker.views.generic_object import (
    GenericExamObjectCreateView,
    GenericExamObjectUpdateView,
    GenericExamObjectDeleteView,
)

from report_maker.views.exam_public_road import (
    PublicRoadExamObjectCreateView,
    PublicRoadExamObjectUpdateView,
    PublicRoadExamObjectDeleteView,
)

from report_maker.views.images import (
    ObjectImageCreateView,
    ObjectImageUpdateView,
    ObjectImageDeleteView,
    images_reorder,
)

app_name = "report_maker"

urlpatterns = [
    # ─────────────────────────────────────
    # Laudos
    # ─────────────────────────────────────
    path("reports/", ReportCaseListView.as_view(), name="reportcase_list"),
    path("reports/create/", ReportCaseCreateView.as_view(), name="reportcase_create"),
    path("reports/<uuid:pk>/", ReportCaseDetailView.as_view(), name="reportcase_detail"),
    path("reports/<uuid:pk>/preview/", ReportCasePreviewView.as_view(), name="reportcase_preview"),
    path("reports/<uuid:pk>/edit/", ReportCaseUpdateView.as_view(), name="reportcase_update"),
    path("reports/<uuid:pk>/delete/", ReportCaseDeleteView.as_view(), name="reportcase_delete"),
    path("reports/<uuid:pk>/close/", ReportCaseCloseView.as_view(), name="reportcase_close"),

    # ─────────────────────────────────────
    # Dashboard para adicionar objetos de exame
    # ─────────────────────────────────────
    path(
        "reports/<uuid:pk>/objects/add/",
        ExamObjectDashboardView.as_view(),
        name="exam_object_dashboard",
    ),

    # ─────────────────────────────────────
    # Objetos de exame (genérico)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_pk>/objects/generic/create/",
        GenericExamObjectCreateView.as_view(),
        name="generic_object_create",
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
    # Objetos de exame (Via Pública)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_pk>/objects/public-road/create/",
        PublicRoadExamObjectCreateView.as_view(),
        name="public_road_object_create",
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
    # Reorder GLOBAL de objetos (ExamObject)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:pk>/exam-objects/reorder/",
        exam_objects_reorder,
        name="exam_objects_reorder",
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
