from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404

from common.form_mixins import CanEditReportsRequiredMixin

from report_maker.forms import ReportCaseForm
from report_maker.models import ReportCase


class ReportCaseListView(LoginRequiredMixin, ListView):
    model = ReportCase
    template_name = "report_maker/reportcase_list.html"
    context_object_name = "reports"
    ordering = ["-updated_at"]

    def get_queryset(self):
        return ReportCase.objects.filter(author=self.request.user)


class ReportCaseCreateView(LoginRequiredMixin, CanEditReportsRequiredMixin, CreateView):
    model = ReportCase
    form_class = ReportCaseForm
    template_name = "report_maker/reportcase_form.html"
    success_url = reverse_lazy("report_maker:report_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ReportCaseUpdateView(LoginRequiredMixin, CanEditReportsRequiredMixin, UpdateView):
    model = ReportCase
    form_class = ReportCaseForm
    template_name = "report_maker/reportcase_form.html"

    def get_queryset(self):
        return ReportCase.objects.filter(author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("report_maker:report_detail", kwargs={"pk": self.object.pk})


class ReportCaseDetailView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        from django.db.models import Prefetch
        from report_maker.models import GenericExamObject, ObjectImage  # ajuste os imports conforme seus nomes reais

        return (
            ReportCase.objects
            .filter(author=self.request.user)
            .prefetch_related(
                Prefetch(
                    "exam_objects",
                    queryset=GenericExamObject.objects.order_by("order", "created_at").prefetch_related(
                        Prefetch("images", queryset=ObjectImage.objects.order_by("index", "created_at"))
                    ),
                )
            )
        )

class ReportCaseDeleteView(LoginRequiredMixin, CanEditReportsRequiredMixin, DeleteView):
    model = ReportCase
    template_name = "report_maker/reportcase_confirm_delete.html"
    context_object_name = "report"

    def get_object(self, queryset=None):
        report = get_object_or_404(ReportCase, pk=self.kwargs["pk"])

        if not report.can_edit:
            raise Http404("Você não tem permissão para excluir este laudo.")

        return report

    def get_success_url(self):
        return reverse_lazy("report_maker:report_list")
