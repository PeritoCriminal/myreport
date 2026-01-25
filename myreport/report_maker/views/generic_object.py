# myreport/report_maker/views/generic_object.py

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from report_maker.forms import GenericExamObjectForm

from report_maker.models import ReportCase, GenericExamObject




# ─────────────────────────────────────────────────────────────
# Helpers / Mixins
# ─────────────────────────────────────────────────────────────

class ReportCaseOwnedMixin:
    """
    Carrega o ReportCase e garante que pertence ao usuário autenticado.
    """
    report_pk_url_kwarg = "report_pk"

    def get_report_case(self) -> ReportCase:
        pk = self.kwargs.get(self.report_pk_url_kwarg)
        if not pk:
            raise Http404("ReportCase não informado.")
        try:
            report = ReportCase.objects.select_related("author").get(pk=pk)
        except ReportCase.DoesNotExist:
            raise Http404("ReportCase não encontrado.")
        if report.author_id != self.request.user.id:
            raise PermissionDenied("Acesso negado.")
        return report


class CanEditReportRequiredMixin(ReportCaseOwnedMixin):
    """
    Bloqueia ações de escrita quando o ReportCase não puder ser editado.
    """
    def dispatch(self, request, *args, **kwargs):
        self.report_case = self.get_report_case()
        if not self.report_case.can_edit:
            raise PermissionDenied("Este laudo está bloqueado para edição.")
        return super().dispatch(request, *args, **kwargs)


class GenericExamObjectOwnedQuerySetMixin:
    """
    Garante que o objeto (GenericExamObject) pertence ao usuário via report_case.author.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("report_case").filter(report_case__author=self.request.user)


# ─────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────

class GenericExamObjectCreateView(CanEditReportRequiredMixin, CreateView):
    model = GenericExamObject
    template_name = "report_maker/generic_object_form.html"
    form_class = GenericExamObjectForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report_case
        ctx["mode"] = "create"
        return ctx

    def form_valid(self, form):
        form.instance.report_case = self.report_case
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class GenericExamObjectUpdateView(
    CanEditReportRequiredMixin,
    GenericExamObjectOwnedQuerySetMixin,
    UpdateView,
):
    model = GenericExamObject
    template_name = "report_maker/generic_object_form.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"
    form_class = GenericExamObjectForm

    def dispatch(self, request, *args, **kwargs):
        # report_case é usado no context + success_url
        self.report_case = self.get_report_case()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.report_case_id != self.report_case.id:
            raise PermissionDenied("Objeto não pertence a este laudo.")
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report_case
        ctx["mode"] = "update"
        return ctx

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class GenericExamObjectDeleteView(
    CanEditReportRequiredMixin,
    GenericExamObjectOwnedQuerySetMixin,
    DeleteView,
):
    model = GenericExamObject
    template_name = "report_maker/generic_object_confirm_delete.html"
    context_object_name = "obj"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        self.report_case = self.get_report_case()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.report_case_id != self.report_case.id:
            raise PermissionDenied("Objeto não pertence a este laudo.")
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report_case
        return ctx

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})

