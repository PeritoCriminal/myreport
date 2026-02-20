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
    Contexto-padrão para CRUD de ReportTextBlock.

    Responsabilidades:
    1) Resolver o ReportCase pelo parâmetro de URL (por padrão: report_pk).
    2) Restringir acesso ao autor do laudo (não “vaza” existência: devolve 404).
    3) Em operações de escrita (POST/PUT/PATCH/DELETE), bloquear se o laudo não
       estiver editável (report.can_edit == False).

    Cache:
    - expõe `self.report_case` para as views filhas.
    - injeta `report` no context para templates.

    Observação de segurança:
    - Usa Http404 em vez de PermissionDenied para não expor que o laudo existe
      para usuários que não são o autor (padrão consistente com outras views).
    """

    report_pk_url_kwarg = "report_pk"
    report_case: ReportCase | None = None

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

        is_write = request.method in ("POST", "PUT", "PATCH", "DELETE")
        if is_write and not getattr(self.report_case, "can_edit", False):
            # 404 para não revelar detalhes; UX pode mostrar msg em outra camada
            raise Http404("Laudo bloqueado para edição.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = self.report_case
        return ctx


class ReportTextBlockListView(LoginRequiredMixin, ReportCaseContextMixin, ListView):
    """
    Lista os blocos de texto do laudo.

    Observação:
    - Não altera nada; apenas lê.
    - A ordenação prioriza estabilidade e previsibilidade no template.
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

    Regras de integridade (UX + segurança):
    - `placement` pode ser “travado” via querystring (?placement=...).
    - Para OBJECT_GROUP_INTRO, `group_key` pode ser “travado” via querystring
      (?group_key=...).
    - Em POST, re-trava os mesmos campos para não confiar no payload.
    """
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_form.html"
    form_class = ReportTextBlockForm

    def get_initial(self):
        initial = super().get_initial()

        placement = (self.request.GET.get("placement") or "").strip()
        if placement:
            initial["placement"] = placement

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            group_key = (self.request.GET.get("group_key") or "").strip()
            if group_key:
                initial["group_key"] = group_key

        # INJEÇÃO DO PREÂMBULO
        if placement == "PREAMBLE":
            # A property preamble do modelo ReportCase gera o texto formatado
            # injetamos no campo 'body' do formulário
            initial["body"] = self.report_case.preamble

        # Injeta APENAS no create (GET) e apenas se o body estiver vazio
        if placement == ReportTextBlock.Placement.CONCLUSION:
            author = getattr(self.report_case, "author", None)
            closing = (getattr(author, "closing_phrase", "") or "").strip()
            if closing and not (initial.get("body") or "").strip():
                initial["body"] = f"\n\n*{closing}*"

        return initial


    def get_form(self, form_class=None):
        """
        Ajusta a instância ANTES de renderizar o form (GET) para:
        - setar report_case;
        - travar placement e, se aplicável, group_key.
        """
        form = super().get_form(form_class)
        form.instance.report_case = self.report_case

        placement = (form.initial.get("placement") or self.request.GET.get("placement") or "").strip()
        if placement:
            form.instance.placement = placement

        if placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO:
            group_key = (form.initial.get("group_key") or self.request.GET.get("group_key") or "").strip()
            form.instance.group_key = group_key

        return form

    def form_valid(self, form):
        """
        Reforça a amarração de segurança no POST.
        """
        form.instance.report_case = self.report_case

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
        context = super().get_context_data(**kwargs)
        
        # Busca o valor do objeto (se edição) ou da URL (se criação)
        placement = getattr(self.object, 'placement', self.request.GET.get('placement', ''))
        group_key = getattr(self.object, 'group_key', self.request.GET.get('group_key', ''))

        # Labels para o cabeçalho
        context["placement_label"] = dict(ReportTextBlock.Placement.choices).get(placement, placement)
        context["current_placement"] = placement
        context["current_group_key"] = group_key
        
        # URL de cancelamento (ajuste o nome da sua url se necessário)
        context["cancel_url"] = reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
        
        return context


class ReportTextBlockUpdateView(LoginRequiredMixin, ReportCaseContextMixin, UpdateView):
    """
    Edita um bloco de texto do laudo.

    Regras de integridade:
    - O bloco só pode ser editado se pertencer ao ReportCase do URL.
    - `placement` e `group_key` NÃO podem ser alterados no update (travados).
    """
    model = ReportTextBlock
    template_name = "report_maker/report_text_block_form.html"
    form_class = ReportTextBlockForm
    pk_url_kwarg = "pk"

    def get_queryset(self):
        # Garante que não “puxe” block de outro laudo por troca de pk
        return super().get_queryset().filter(report_case=self.report_case)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.report_case = self.report_case

        # trava por segurança (GET)
        form.instance.placement = self.object.placement
        form.instance.group_key = self.object.group_key
        return form

    def form_valid(self, form):
        form.instance.report_case = self.report_case

        # re-trava no POST
        form.instance.placement = self.object.placement
        form.instance.group_key = self.object.group_key
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Busca o valor do objeto (se edição) ou da URL (se criação)
        placement = getattr(self.object, 'placement', self.request.GET.get('placement', ''))
        group_key = getattr(self.object, 'group_key', self.request.GET.get('group_key', ''))

        # Labels para o cabeçalho
        context["placement_label"] = dict(ReportTextBlock.Placement.choices).get(placement, placement)
        context["current_placement"] = placement
        context["current_group_key"] = group_key
        
        # URL de cancelamento (ajuste o nome da sua url se necessário)
        context["cancel_url"] = reverse("report_maker:reportcase_detail", kwargs={"pk": self.report_case.pk})
        
        return context


class ReportTextBlockDeleteView(LoginRequiredMixin, ReportCaseContextMixin, DeleteView):
    """
    Exclui um bloco de texto do laudo.

    Observação:
    - O queryset é filtrado por report_case, evitando deletar bloco de outro laudo.
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
    “Upsert” de bloco de texto:
    - se existir, redireciona para edição;
    - se não existir, redireciona para criação com querystring.

    Útil para:
    - placements únicos (ex.: SUMMARY, TOC, CONCLUSION...);
    - textos por grupo (OBJECT_GROUP_INTRO), onde a chave do grupo é obrigatória.

    Regras:
    - OBJECT_GROUP_INTRO exige group_key; sem isso, volta ao detail do laudo.
    """

    def get(self, request, *args, **kwargs):
        placement = (kwargs.get("placement") or "").strip()
        group_key = (request.GET.get("group_key") or "").strip()

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

        if group_key:
            return redirect(f"{create_url}?placement={placement}&group_key={group_key}")
        return redirect(f"{create_url}?placement={placement}")

    @staticmethod
    def get_placement_label(placement: str) -> str:
        """Label humano para exibição no template."""
        return dict(ReportTextBlock.Placement.choices).get(placement, placement)

    @staticmethod
    def get_group_label(group_key: str) -> str:
        """Label humano do grupo para exibição no template."""
        return dict(ExamObjectGroup.choices).get(group_key, group_key)
