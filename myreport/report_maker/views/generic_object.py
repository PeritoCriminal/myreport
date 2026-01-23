"""
Views de CRUD para objetos de exame genéricos (GenericExamObject).

Garantias:
- acesso restrito ao autor do laudo;
- bloqueio de edição/exclusão quando o laudo não puder ser editado;
- ordenação automática delegada ao model (ExamObject.save).
"""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from common.mixins import ExamObjectMetaContextMixin, CanEditReportsRequiredMixin
from report_maker.forms import GenericExamObjectForm
from report_maker.models import GenericExamObject, ReportCase


class GenericExamObjectCreateView(
    LoginRequiredMixin,
    CanEditReportsRequiredMixin,
    CreateView,
):
    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"

    def get_report_case(self) -> ReportCase:
        report_pk = self.kwargs.get("report_pk") or self.kwargs.get("pk")
        report = ReportCase.objects.filter(
            author=self.request.user,
            pk=report_pk,
        ).first()
        if not report or not report.can_edit:
            raise Http404
        return report

    def form_valid(self, form):
        form.instance.report_case = self.get_report_case()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )


class GenericExamObjectUpdateView(
    LoginRequiredMixin,
    CanEditReportsRequiredMixin,
    UpdateView,
):
    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"
    context_object_name = "obj"

    def get_queryset(self):
        return GenericExamObject.objects.filter(
            report_case__author=self.request.user
        )

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.report_case.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )


class GenericExamObjectDeleteView(
    LoginRequiredMixin,
    CanEditReportsRequiredMixin,
    DeleteView,
):
    model = GenericExamObject
    template_name = "report_maker/generic_object_confirm_delete.html"
    context_object_name = "obj"

    def get_queryset(self):
        return GenericExamObject.objects.filter(
            report_case__author=self.request.user
        )

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.report_case.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )


class GenericExamObjectDetailView(
    ExamObjectMetaContextMixin,
    LoginRequiredMixin,
    DetailView,
):
    model = GenericExamObject
    template_name = "report_maker/generic_object_detail.html"
    context_object_name = "obj"

    def get_queryset(self):
        return super().get_queryset().filter(
            report_case__author=self.request.user
        )


@login_required
@require_POST
@csrf_protect
def generic_object_reorder(request, pk):
    """
    Reordena objetos de exame de um laudo com base em uma lista ordenada de UUIDs.
    """
    report = ReportCase.objects.filter(
        pk=pk,
        author=request.user,
    ).first()
    if not report or not report.can_edit:
        raise Http404

    try:
        data = json.loads(request.body.decode("utf-8"))
        ordered_ids = data.get("ordered_ids", [])
        if not isinstance(ordered_ids, list) or not ordered_ids:
            return JsonResponse(
                {"ok": False, "error": "ordered_ids inválido"},
                status=400,
            )
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"ok": False, "error": "JSON inválido"},
            status=400,
        )

    qs = GenericExamObject.objects.filter(
        report_case=report,
        pk__in=ordered_ids,
    )
    if qs.count() != len(ordered_ids):
        return JsonResponse(
            {"ok": False, "error": "IDs não pertencem ao laudo"},
            status=400,
        )

    with transaction.atomic():
        for idx, obj_id in enumerate(ordered_ids, start=1):
            GenericExamObject.objects.filter(
                report_case=report,
                pk=obj_id,
            ).update(order=idx)

    return JsonResponse({"ok": True})
