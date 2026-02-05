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
from report_maker.views.report_case_showpage import ReportCaseShowPageView
from report_maker.views.report_pdf_generator import reportPDFGenerator

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

from report_maker.views.exam_generic_location import(
    GenericLocationExamObjectCreateView,
    GenericLocationExamObjectUpdateView,
    GenericLocationExamObjectDeleteView,
)

from report_maker.views.vehicle_inspection_views import (
    # VehicleInspectionListView,
    # VehicleInspectionDetailView,
    VehicleInspectionCreateView,
    VehicleInspectionUpdateView,
    VehicleInspectionDeleteView,
)

from report_maker.views.images import (
    ObjectImageCreateView,
    ObjectImageUpdateView,
    ObjectImageDeleteView,
    images_reorder,
)

# ─────────────────────────────────────
# Textos genéricos do laudo (ReportTextBlock)
# ─────────────────────────────────────
from report_maker.views.report_text_block import (
    ReportTextBlockListView,
    ReportTextBlockCreateView,
    ReportTextBlockUpdateView,
    ReportTextBlockDeleteView,
    ReportTextBlockUpsertView,
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
    path("reports/<uuid:pk>/showpage/", ReportCaseShowPageView.as_view(), name="reportcase_showpage"),
    path("reports/<uuid:pk>/edit/", ReportCaseUpdateView.as_view(), name="reportcase_update"),
    path("reports/<uuid:pk>/delete/", ReportCaseDeleteView.as_view(), name="reportcase_delete"),
    path("reports/<uuid:pk>/close/", ReportCaseCloseView.as_view(), name="reportcase_close"),
    path("reports/<uuid:pk>/pdf/", reportPDFGenerator, name="report_pdf"),


    # ─────────────────────────────────────
    # Textos do laudo (ReportTextBlock)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_pk>/text-blocks/",
        ReportTextBlockListView.as_view(),
        name="textblock_list",
    ),
    path(
        "reports/<uuid:report_pk>/text-blocks/create/",
        ReportTextBlockCreateView.as_view(),
        name="textblock_create",
    ),
    path(
        "reports/<uuid:report_pk>/text-blocks/<uuid:pk>/edit/",
        ReportTextBlockUpdateView.as_view(),
        name="textblock_update",
    ),
    path(
        "reports/<uuid:report_pk>/text-blocks/<uuid:pk>/delete/",
        ReportTextBlockDeleteView.as_view(),
        name="textblock_delete",
    ),
    path(
        "reports/<uuid:report_pk>/text-blocks/<str:placement>/",
        ReportTextBlockUpsertView.as_view(),
        name="text_block_upsert",
    ),

    # ─────────────────────────────────────
    # Dashboard para adicionar objetos de exame
    # ─────────────────────────────────────
    path(
        "reports/<uuid:pk>/objects/add/",
        ExamObjectDashboardView.as_view(),
        name="exam_object_dashboard",
    ),

    path("images/reorder/", images_reorder, name="images_reorder"),

    # ─────────────────────────────────────
    # Objetos de exame (genérico)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_pk>/objects/generic/create/",
        GenericExamObjectCreateView.as_view(),
        name="generic_object_create",
    ),
    path(
        "reports/<uuid:report_pk>/objects/generic/<uuid:pk>/edit/",
        GenericExamObjectUpdateView.as_view(),
        name="generic_object_update",
    ),
    path(
        "reports/<uuid:report_pk>/objects/generic/<uuid:pk>/delete/",
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
        "reports/<uuid:report_pk>/objects/public-road/<uuid:pk>/edit/",
        PublicRoadExamObjectUpdateView.as_view(),
        name="public_road_object_update",
    ),
    path(
        "reports/<uuid:report_pk>/objects/public-road/<uuid:pk>/delete/",
        PublicRoadExamObjectDeleteView.as_view(),
        name="public_road_object_delete",
    ),

    # ─────────────────────────────────────
    # Objetos de exame (Via Pública)
    # ─────────────────────────────────────
    path(
        "reports/<uuid:report_pk>/objects/generic-location/create/",
        GenericLocationExamObjectCreateView.as_view(),
        name="generic_exam_location_object_create",
    ),
    path(
        "reports/<uuid:report_pk>/objects/generic-location/<uuid:pk>/edit/",
        GenericLocationExamObjectUpdateView.as_view(),
        name="generic_location_update",
    ),
    path(
        "reports/<uuid:report_pk>/objects/generic-location/<uuid:pk>/delete/",
        GenericLocationExamObjectDeleteView.as_view(),
        name="generic_location_delete",
    ),

    # ─────────────────────────────────────
    # Objetos de exame (Vistoria de Veículo)
    # ─────────────────────────────────────
    #path(
    #    "reports/<uuid:report_pk>/objects/vehicles/",
    #    VehicleInspectionListView.as_view(),
    #    name="vehicle_inspection_list",
    #),
    path(
        "reports/<uuid:report_pk>/objects/vehicles/create/",
        VehicleInspectionCreateView.as_view(),
        name="vehicle_inspection_create",
    ),
    #path(
    #    "reports/<uuid:report_pk>/objects/vehicles/<uuid:pk>/",
    #    VehicleInspectionDetailView.as_view(),
    #    name="vehicle_inspection_detail",
    #),
    path(
        "reports/<uuid:report_pk>/objects/vehicles/<uuid:pk>/edit/",
        VehicleInspectionUpdateView.as_view(),
        name="vehicle_inspection_update",
    ),
    path(
        "reports/<uuid:report_pk>/objects/vehicles/<uuid:pk>/delete/",
        VehicleInspectionDeleteView.as_view(),
        name="vehicle_inspection_delete",
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
