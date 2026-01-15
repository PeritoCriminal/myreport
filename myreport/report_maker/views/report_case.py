from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404

from common.form_mixins import CanEditReportsRequiredMixin
from report_maker.forms import ReportCaseForm
from report_maker.models import ReportCase

def _resolve(value):
    return value() if callable(value) else value

def _get_user_org(user):
    inst_asg = _resolve(getattr(user, "active_institution_assignment", None))
    team_asg = _resolve(getattr(user, "active_team_assignment", None))

    team = getattr(team_asg, "team", None)

    institution = (
        getattr(inst_asg, "institution", None)
        or getattr(team_asg, "institution", None)
    )

    nucleus = (
        getattr(inst_asg, "nucleus", None)
        or getattr(team_asg, "nucleus", None)
        or (getattr(team, "nucleus", None) if team else None)
    )

    return institution, nucleus, team


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

        institution, nucleus, team = _get_user_org(self.request.user)
        form.instance.institution = institution
        form.instance.nucleus = nucleus
        form.instance.team = team

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

    def form_valid(self, form):
        """
        Se o laudo ainda não tiver vínculos preenchidos, preenche automaticamente
        a partir das assignments do usuário.
        """
        obj = form.save(commit=False)

        if obj.institution_id is None and obj.nucleus_id is None and obj.team_id is None:
            institution, nucleus, team = _get_user_org(self.request.user)
            obj.institution = institution
            obj.nucleus = nucleus
            obj.team = team

        obj.save()
        self.object = obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:report_detail", kwargs={"pk": self.object.pk})


class ReportCaseDetailView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        from django.db.models import Prefetch
        from report_maker.models import GenericExamObject, ObjectImage  # ajuste conforme seus nomes reais

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
