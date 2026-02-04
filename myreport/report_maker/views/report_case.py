# report_maker/views/report_case.py

from __future__ import annotations

from collections import OrderedDict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Count
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from report_maker.models import ReportCase, ObjectImage, ReportTextBlock, ExamObjectGroup
from report_maker.forms.report_case import ReportCaseForm
from report_maker.models.images import ObjectImage

from report_maker.views.report_outline import build_report_outline

# ─────────────────────────────────────────────────────────────
# Mixin
# ─────────────────────────────────────────────────────────────

class ReportCaseAuthorQuerySetMixin:
    """
    Garante que o usuário só enxergue/manipule laudos próprios.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)


class ReportCaseCanEditRequiredMixin:
    """
    Bloqueia edição/exclusão quando o laudo não puder ser editado.
    Usa a regra de domínio: ReportCase.can_edit.
    """
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_edit:
            raise PermissionDenied("Este laudo está bloqueado para edição.")
        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────
# LIST / DETAIL
# ─────────────────────────────────────────────────────────────

# Se na view abaixo eu puder filtrar e criar uma lista com os laudos,
# la no template poderei iterar sobre essa lista? Isso já é feito aqui mas eu não vejo?
class ReportCaseListView(LoginRequiredMixin, ListView):
    model = ReportCase
    template_name = "report_maker/reportcase_list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        return (
            ReportCase.objects
            .filter(author=self.request.user)
            .select_related("institution", "nucleus", "team", "author")
            .order_by("-updated_at")
        ) 



class ReportCaseDetailView(LoginRequiredMixin, ReportCaseAuthorQuerySetMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_detail.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        images_qs = ObjectImage.objects.order_by("index", "id")

        exam_objects_qs = (
            report.exam_objects.all()
            .prefetch_related(Prefetch("images", queryset=images_qs))
            .order_by("order", "created_at")
        )
        ctx["exam_objects"] = exam_objects_qs

        # Textos do laudo
        text_blocks_qs = report.text_blocks.all().order_by("placement", "position", "created_at")
        ctx["text_blocks"] = text_blocks_qs

        ctx["text_blocks_by_placement"] = {
            k: list(text_blocks_qs.filter(placement=k))
            for k, _ in ReportTextBlock.Placement.choices
        }

        # Preâmbulo: usuário > sistema
        preamble_text = (
            text_blocks_qs.filter(placement=ReportTextBlock.Placement.PREAMBLE)
            .values_list("body", flat=True)
            .first()
        )
        ctx["preamble"] = (preamble_text or "").strip() or report.preamble

        # Dropdown: "texto comum do grupo" (>=2 objetos)
        counts = (
            report.exam_objects.exclude(group_key__isnull=True)
            .exclude(group_key="")
            .values("group_key")
            .annotate(n=Count("id"))
        )
        count_map = {row["group_key"]: row["n"] for row in counts}

        ctx["editorial_groups"] = [
            {"key": key, "label": label}
            for key, label in ExamObjectGroup.choices
            if count_map.get(key, 0) >= 2
        ]

        # Outline (showpage/pdf)  ✅ build_report_outline retorna (outline, n_top)
        outline, _n_top = build_report_outline(
            report=report,
            exam_objects_qs=exam_objects_qs,
            text_blocks_qs=text_blocks_qs,
            start_at=1,
            prepend_blocks=report.get_render_blocks(),
        )
        ctx["outline"] = outline

        # ─────────────────────────────────────────────────────────────
        # Intros por grupo (OBJECT_GROUP_INTRO)
        # ─────────────────────────────────────────────────────────────
        intro_rows = (
            text_blocks_qs.filter(placement=ReportTextBlock.Placement.OBJECT_GROUP_INTRO)
            .values_list("group_key", "body")
        )
        intro_by_key = {k: (b or "").strip() for k, b in intro_rows if k}

        # Labels por grupo (choices)
        label_by_key = {k: lbl for k, lbl in ExamObjectGroup.choices}

        # Monta grupos “prontos” para o template (sem regroup + sem get_item)
        groups = OrderedDict()
        for obj in list(exam_objects_qs):
            key = (obj.group_key or "").strip() or ExamObjectGroup.OTHER
            groups.setdefault(
                key,
                {
                    "key": key,
                    "label": label_by_key.get(key, "Outros"),
                    "intro_text": intro_by_key.get(key, ""),
                    "objects": [],
                },
            )
            groups[key]["objects"].append(obj)

        # ✅ Ordem editorial fixa dos grupos (detail)
        GROUP_ORDER = [
            ExamObjectGroup.LOCATIONS,
            ExamObjectGroup.VEHICLES,
            ExamObjectGroup.PARTS,
            ExamObjectGroup.CADAVERS,
            ExamObjectGroup.OTHER,  # sempre por último
        ]
        GROUP_RANK = {k: i for i, k in enumerate(GROUP_ORDER)}

        def _group_sort_key(k: str) -> tuple[int, str]:
            if k in GROUP_RANK:
                return (GROUP_RANK[k], k)
            return (9_000, k)  # fallback p/ grupos inesperados

        ctx["exam_groups_ui"] = [groups[k] for k in sorted(groups.keys(), key=_group_sort_key)]

        return ctx



# ─────────────────────────────────────────────────────────────
# CREATE / UPDATE / DELETE
# ─────────────────────────────────────────────────────────────

class ReportCaseCreateView(LoginRequiredMixin, CreateView):
    model = ReportCase
    template_name = "report_maker/reportcase_form.html"
    form_class = ReportCaseForm  # <- aqui

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("report_maker:reportcase_detail", kwargs={"pk": self.object.pk})


class ReportCaseUpdateView(
    LoginRequiredMixin,
    ReportCaseAuthorQuerySetMixin,
    ReportCaseCanEditRequiredMixin,
    UpdateView,
):
    model = ReportCase
    template_name = "report_maker/reportcase_form.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"
    form_class = ReportCaseForm  # <- aqui

    def get_success_url(self):
        return reverse_lazy("report_maker:reportcase_detail", kwargs={"pk": self.object.pk})


class ReportCaseDeleteView(
    LoginRequiredMixin,
    ReportCaseAuthorQuerySetMixin,
    ReportCaseCanEditRequiredMixin,
    DeleteView,
):
    model = ReportCase 
    template_name = "report_maker/reportcase_confirm_delete.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("report_maker:reportcase_list")
