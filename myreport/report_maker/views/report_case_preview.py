# report_maker/views/report_case_preview.py
from __future__ import annotations

from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.views.generic import DetailView

from report_maker.models import (
    ReportCase,
    GenericExamObject,
    PublicRoadExamObject,
    ObjectImage,
)


class ReportCasePreviewView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_preview.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        # apenas o autor pode ver o preview
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

        # o template do preview pode iterar por "exam_objects"
        context["exam_objects"] = merged
        return context
