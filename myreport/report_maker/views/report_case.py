from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView

from report_maker.models import ReportCase


class ReportCaseListView(LoginRequiredMixin, ListView):
    """
    Lista os laudos vinculados ao usuário autenticado.
    """

    model = ReportCase
    template_name = "report_maker/reportcase_list.html"
    context_object_name = "reports"
    ordering = ["-updated_at"]

    def get_queryset(self):
        return ReportCase.objects.filter(author=self.request.user)


class ReportCaseCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de novo laudo pericial.
    """

    model = ReportCase
    template_name = "report_maker/reportcase_form.html"
    fields = [
        "report_number",
        "protocol",
        "objective",
        "requesting_authority",
        "police_report",
        "police_inquiry",
        "police_station",
        "occurrence_datetime",
        "assignment_datetime",
        "examination_datetime",
        "photography_by",
        "sketch_by",
    ]
    success_url = reverse_lazy("report_maker:report_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ReportCaseDetailView(LoginRequiredMixin, DetailView):
    """
    Exibição detalhada do laudo pericial.
    """

    model = ReportCase
    template_name = "report_maker/reportcase_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        return ReportCase.objects.filter(author=self.request.user)
