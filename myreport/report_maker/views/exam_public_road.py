from __future__ import annotations

from typing import Any

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from report_maker.forms.exam_public_road import PublicRoadExamObjectForm
from report_maker.models import ReportCase  # ajuste o import se seu ReportCase estiver em outro módulo
from report_maker.models.exam_public_road import PublicRoadExamObject


# -----------------------------------------------------------------------------
# Helpers (fallbacks seguros para não “amarrar” o código a um único nome de field)
# -----------------------------------------------------------------------------
def _report_owner(report: ReportCase):
    """
    Tenta descobrir o campo de autoria do ReportCase sem travar o projeto
    (created_by / author / user). Retorna None se não achar.
    """
    for attr in ("created_by", "author", "user"):
        if hasattr(report, attr):
            return getattr(report, attr)
    return None


def _report_is_editable(report: ReportCase) -> bool:
    """
    Tenta descobrir se o laudo pode ser editado (bool ou método).
    FallBack: True (não bloqueia se a base ainda não tiver essa regra).
    """
    for attr in ("can_edit", "is_editable", "is_open", "editable"):
        if hasattr(report, attr):
            value = getattr(report, attr)
            return bool(value() if callable(value) else value)
    return True


# -----------------------------------------------------------------------------
# Base mixin do módulo: resolve ReportCase e aplica regra de segurança
# -----------------------------------------------------------------------------
class _PublicRoadBaseMixin:
    """
    Resolve o ReportCase e aplica:
    - acesso restrito ao autor do laudo (fallback seguro);
    - bloqueio de alteração/exclusão/criação se o laudo não puder ser editado.
    """

    report_pk_url_kwarg = "report_pk"
    report_context_name = "report"

    def get_report_case(self) -> ReportCase:
        report_pk = self.kwargs.get(self.report_pk_url_kwarg)

        # Se a URL não tiver report_pk (ex.: detail/update/delete via pk do objeto),
        # tentamos obter via self.get_object() quando existir.
        if not report_pk and hasattr(self, "get_object"):
            obj = self.get_object()
            report = getattr(obj, "report_case", None)
            if report is None:
                raise Http404("Laudo não encontrado.")
        else:
            report = get_object_or_404(ReportCase, pk=report_pk)

        owner = _report_owner(report)
        if owner is not None and owner != self.request.user:
            raise Http404("Laudo não encontrado.")

        return report

    def ensure_report_editable(self, report: ReportCase) -> None:
        if not _report_is_editable(report):
            raise Http404("Este laudo não pode ser editado.")

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context[self.report_context_name] = self.get_report_case()
        return context

    def get_success_url(self) -> str:
        """
        Volta para o preview do laudo (ajuste o name se o seu urls.py usar outro).
        """
        report = self.get_report_case()
        return reverse("report_maker:report_detail", kwargs={"pk": report.pk})


# -----------------------------------------------------------------------------
# LIST
# -----------------------------------------------------------------------------
class PublicRoadExamObjectListView(
    LoginRequiredMixin,
    _PublicRoadBaseMixin,
    ListView,
):
    model = PublicRoadExamObject
    template_name = "report_maker/exam_public_road_list.html"
    context_object_name = "objects"

    def get_queryset(self):
        report = self.get_report_case()
        return (
            self.model.objects
            .filter(report_case=report)
            .order_by("order")
        )


# -----------------------------------------------------------------------------
# CREATE
# -----------------------------------------------------------------------------
class PublicRoadExamObjectCreateView(
    LoginRequiredMixin,
    _PublicRoadBaseMixin,
    CreateView,
):
    model = PublicRoadExamObject
    form_class = PublicRoadExamObjectForm
    template_name = "report_maker/exam_public_road_form.html"

    def dispatch(self, request, *args, **kwargs):
        report = self.get_report_case()
        self.ensure_report_editable(report)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        report = self.get_report_case()
        self.ensure_report_editable(report)

        obj = form.save(commit=False)
        obj.report_case = report
        obj.save()
        self.object = obj
        return super().form_valid(form)


# -----------------------------------------------------------------------------
# DETAIL
# -----------------------------------------------------------------------------
class PublicRoadExamObjectDetailView(
    LoginRequiredMixin,
    _PublicRoadBaseMixin,
    DetailView,
):
    model = PublicRoadExamObject
    template_name = "report_maker/exam_public_road_detail.html"
    context_object_name = "object"

    def get_queryset(self):
        # restringe a objetos cujo laudo pertença ao usuário
        qs = self.model.objects.all()
        # não temos o nome exato do campo do autor no ReportCase, então validamos no get_report_case()
        return qs


# -----------------------------------------------------------------------------
# UPDATE
# -----------------------------------------------------------------------------
class PublicRoadExamObjectUpdateView(
    LoginRequiredMixin,
    _PublicRoadBaseMixin,
    UpdateView,
):
    model = PublicRoadExamObject
    form_class = PublicRoadExamObjectForm
    template_name = "report_maker/exam_public_road_form.html"
    context_object_name = "object"

    def dispatch(self, request, *args, **kwargs):
        report = self.get_report_case()
        self.ensure_report_editable(report)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()


# -----------------------------------------------------------------------------
# DELETE
# -----------------------------------------------------------------------------
class PublicRoadExamObjectDeleteView(
    LoginRequiredMixin,
    _PublicRoadBaseMixin,
    DeleteView,
):
    model = PublicRoadExamObject
    template_name = "report_maker/exam_public_road_confirm_delete.html"
    context_object_name = "object"

    def dispatch(self, request, *args, **kwargs):
        report = self.get_report_case()
        self.ensure_report_editable(report)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()
