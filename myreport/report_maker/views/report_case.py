# report_maker/views/report_case.py

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from report_maker.forms.report_case import ReportCaseForm
from report_maker.models import ReportCase
from report_maker.models.images import ObjectImage




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

        ctx["exam_objects"] = (
            report.exam_objects.all()
            .prefetch_related(Prefetch("images", queryset=images_qs))
            .order_by("order", "created_at")
        )

        ctx["text_blocks"] = (
            report.text_blocks.all()
            .order_by("placement", "order", "created_at")
        )

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
