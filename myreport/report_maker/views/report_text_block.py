# report_maker/views/report_text_block.py

from __future__ import annotations

from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from report_maker.forms import ReportTextBlockForm
from report_maker.models import ReportCase
from report_maker.models.report_text_block import ReportTextBlock

from report_maker.models.exam_base import ExamObjectGroup


class ReportCaseContextMixin:
    """
    Carrega o ReportCase a partir do URL e expõe em `self.report_case`.

    Restringe o acesso ao autor do laudo. Em métodos de escrita, bloqueia
    a operação quando o laudo não estiver editável.
    """

    report_pk_url_kwarg = "report_pk"

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get(self.report_pk_url_kwarg)
        if not pk:
            raise Http404("ReportCase não informado.")

        try:
            self.report_case = (
                ReportCase.objects
                .select_related("author")
                .get(pk=pk, author=request.user)
            )
        except ReportCase.DoesNotExist:
            raise Http404("Laudo não encontrado.")

        if request.method in ("POST", "PUT", "PATCH", "DELETE") and not self.report_case.can_edit:
            raise Http404("Laudo bloqueado para edição.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report_case
        return ctx


class ReportTextBlockListView(LoginRequiredMixin, ReportCaseContextMixin, ListView):
    """
    Lista os blocos de texto do laudo.
    """
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_list.html"
    context_object_name = "blocks"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(report_case=self.report_case)
            .order_by("placement", "position", "created_at")
        )





class ReportTextBlockCreateView(LoginRequiredMixin, ReportCaseContextMixin, CreateView):
    """
    Cria um bloco de texto no laudo.
    """
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_form.html"
    form_class = ReportTextBlockForm

    def get_initial(self):
        initial = super().get_initial()

        placement = (self.request.GET.get("placement") or "").strip()
        if placement:
            initial["placement"] = placement

        # Se for texto comum do grupo, já deixa group_key no initial também
        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            group_key = (self.request.GET.get("group_key") or "").strip()
            if group_key:
                initial["group_key"] = group_key

        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.report_case = self.report_case

        placement = (form.initial.get("placement") or self.request.GET.get("placement") or "").strip()
        if placement:
            form.instance.placement = placement  # trava

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            group_key = (form.initial.get("group_key") or self.request.GET.get("group_key") or "").strip()
            form.instance.group_key = group_key  # trava

        return form

    def form_valid(self, form):
        form.instance.report_case = self.report_case

        # Segurança: re-trava placement/group_key no POST (não confia no payload)
        placement = (self.request.GET.get("placement") or form.cleaned_data.get("placement") or "").strip()
        if placement:
            form.instance.placement = placement

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            group_key = (self.request.GET.get("group_key") or form.cleaned_data.get("group_key") or "").strip()
            form.instance.group_key = group_key

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        placement = (self.request.GET.get("placement") or "").strip()
        group_key = (self.request.GET.get("group_key") or "").strip()

        ctx["cancel_url"] = reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
        ctx["placement_label"] = dict(ReportTextBlock.Placement.choices).get(placement, placement)

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO and group_key:
            ctx["group_label"] = dict(ExamObjectGroup.choices).get(group_key, group_key)
        else:
            ctx["group_label"] = ""

        return ctx


class ReportTextBlockUpdateView(LoginRequiredMixin, ReportCaseContextMixin, UpdateView):
    """
    Edita um bloco de texto do laudo.
    """
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_form.html"
    form_class = ReportTextBlockForm
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return super().get_queryset().filter(report_case=self.report_case)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.report_case = self.report_case

        # Trava por segurança: não permite “mudar” o tipo/grupo no update
        form.instance.placement = self.object.placement
        form.instance.group_key = self.object.group_key

        return form

    def form_valid(self, form):
        form.instance.report_case = self.report_case

        # Re-trava no POST (não confia no payload)
        form.instance.placement = self.object.placement
        form.instance.group_key = self.object.group_key

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        placement = (self.object.placement or "").strip()
        group_key = (self.object.group_key or "").strip()

        ctx["cancel_url"] = reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
        ctx["placement_label"] = dict(ReportTextBlock.Placement.choices).get(placement, placement)

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO and group_key:
            ctx["group_label"] = dict(ExamObjectGroup.choices).get(group_key, group_key)
        else:
            ctx["group_label"] = ""

        return ctx



class ReportTextBlockDeleteView(LoginRequiredMixin, ReportCaseContextMixin, DeleteView):
    """
    Exclui um bloco de texto do laudo.
    """
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_confirm_delete.html"
    pk_url_kwarg = "pk"
    context_object_name = "block"

    def get_queryset(self):
        return super().get_queryset().filter(report_case=self.report_case)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})


class ReportTextBlockUpsertView(LoginRequiredMixin, ReportCaseContextMixin, View):
    """
    Redireciona para edição caso o bloco exista, ou para criação caso não exista.

    Útil para placements únicos e para textos de grupo (OBJECT_GROUP_INTRO),
    permitindo que o usuário "clique no título" e caia no formulário correto.
    """

    def get(self, request, *args, **kwargs):
        placement = (kwargs.get("placement") or "").strip()
        group_key = (request.GET.get("group_key") or "").strip()

        # Guard simples: não deixa OBJECT_GROUP_INTRO sem group_key
        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO and not group_key:
            return redirect(
                "report_maker:reportcase_detail",
                pk=self.report_case.pk,
            )

        qs = ReportTextBlock.objects.filter(
            report_case=self.report_case,
            placement=placement,
        )

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            qs = qs.filter(group_key=group_key)

        block = qs.first()
        if block:
            return redirect(
                "report_maker:textblock_update",
                report_pk=self.report_case.pk,
                pk=block.pk,
            )

        create_url = reverse(
            "report_maker:textblock_create",
            kwargs={"report_pk": self.report_case.pk},
        )

        # Mantém a UX: cria já com placement/group_key preenchidos via querystring
        if group_key:
            return redirect(f"{create_url}?placement={placement}&group_key={group_key}")
        return redirect(f"{create_url}?placement={placement}")

    @staticmethod
    def get_placement_label(placement: str) -> str:
        # label bonitinho pro template (opcional, mas útil)
        return dict(ReportTextBlock.Placement.choices).get(placement, placement)

    @staticmethod
    def get_group_label(group_key: str) -> str:
        return dict(ExamObjectGroup.choices).get(group_key, group_key)
