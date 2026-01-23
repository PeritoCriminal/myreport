from __future__ import annotations

from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView

from common.mixins import CanEditReportsRequiredMixin, ProfileImageContextMixin
from report_maker.forms import ReportCaseForm
from report_maker.models import (
    ReportCase,
    GenericExamObject,
    PublicRoadExamObject,
    ObjectImage,
)


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


class ReportCaseListView(LoginRequiredMixin, ProfileImageContextMixin, ListView):
    model = ReportCase
    template_name = "report_maker/reportcase_list.html"
    context_object_name = "reports"
    ordering = ["-updated_at"]

    def get_queryset(self):
        return ReportCase.objects.filter(author=self.request.user)


class ReportCaseCreateView(
    LoginRequiredMixin,
    ProfileImageContextMixin,
    CanEditReportsRequiredMixin,
    CreateView,
):
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


class ReportCaseUpdateView(
    LoginRequiredMixin,
    ProfileImageContextMixin,
    CanEditReportsRequiredMixin,
    UpdateView,
):
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


class ReportCaseDetailView(LoginRequiredMixin, ProfileImageContextMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        # Sem "exam_objects": agora os related_names são por-classe (ex.: genericexamobject_objects).
        return ReportCase.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report: ReportCase = context["report"]

        images_qs = ObjectImage.objects.order_by("index", "created_at")

        generic_qs = (
            GenericExamObject.objects
            .filter(report_case=report)
            .order_by("order", "created_at")
            .prefetch_related(Prefetch("images", queryset=images_qs))
        )

        public_road_qs = (
            PublicRoadExamObject.objects
            .filter(report_case=report)
            .order_by("order", "created_at")
            .prefetch_related(Prefetch("images", queryset=images_qs))
        )

        merged = list(chain(generic_qs, public_road_qs))
        merged.sort(key=lambda o: (o.order, o.created_at, str(o.pk)))

        exam_objects_ui = []
        for obj in merged:
            if isinstance(obj, GenericExamObject):
                obj_type = "generic"
                detail_url = reverse("report_maker:generic_object_detail", kwargs={"pk": obj.pk})
            elif isinstance(obj, PublicRoadExamObject):
                obj_type = "public_road"
                detail_url = reverse("report_maker:public_road_object_detail", kwargs={"pk": obj.pk})
            else:
                obj_type = "unknown"
                detail_url = "#"

            exam_objects_ui.append(
                {
                    "obj": obj,
                    "type": obj_type,
                    "detail_url": detail_url,
                }
            )

        context["exam_objects_ui"] = exam_objects_ui
        return context



class ReportCaseDeleteView(
    LoginRequiredMixin,
    ProfileImageContextMixin,
    CanEditReportsRequiredMixin,
    DeleteView,
):
    model = ReportCase
    template_name = "report_maker/reportcase_confirm_delete.html"
    context_object_name = "report"

    def get_queryset(self):
        return ReportCase.objects.filter(author=self.request.user)

    def get_object(self, queryset=None):
        report = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

        if not report.can_edit:
            raise Http404("Você não tem permissão para excluir este laudo.")

        return report

    def get_success_url(self):
        return reverse_lazy("report_maker:report_list")
