"""
Views de CRUD para objetos de exame genéricos (GenericExamObject).

Estas views garantiram:
- acesso restrito ao autor do laudo (report_case__author=request.user);
- bloqueio de edição/exclusão quando o laudo não puder ser editado (report_case.can_edit);
- atribuição automática do campo `order` (sequência de exibição) na criação do objeto.
"""
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Max
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from common.form_mixins import ExamObjectMetaContextMixin

from report_maker.forms import GenericExamObjectForm
from report_maker.models import GenericExamObject, ReportCase


class GenericExamObjectCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um objeto de exame genérico vinculado a um laudo (ReportCase).

    O campo `order` foi atribuído automaticamente, de forma incremental,
    considerando apenas os objetos do mesmo laudo (report_case).
    """

    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"

    def get_report_case(self) -> ReportCase:
        """
        Recuperou o laudo (ReportCase) a partir da URL e validou permissão.

        Esperou-se que a rota de criação incluísse o pk do laudo, por exemplo:
        path("reports/<uuid:report_pk>/objects/new/", ...)

        Ajuste `report_pk` caso o seu kwargs use outro nome.
        """
        report_pk = self.kwargs.get("report_pk") or self.kwargs.get("pk")
        report = ReportCase.objects.filter(author=self.request.user, pk=report_pk).first()
        if not report:
            raise Http404
        if not report.can_edit:
            raise Http404
        return report

    def form_valid(self, form):
        """
        Vinculou o objeto ao laudo e definiu `order` como (maior ordem atual + 1).
        """
        report = self.get_report_case()

        last_order = (
            GenericExamObject.objects.filter(report_case=report)
            .aggregate(max_order=Max("order"))
            .get("max_order")
        )

        form.instance.report_case = report
        form.instance.order = (last_order or 0) + 1

        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirecionou para a página de detalhe do laudo após criar o objeto.
        """
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )


class GenericExamObjectUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editou um objeto genérico, respeitando:
    - acesso restrito ao autor do laudo;
    - bloqueio quando o laudo não puder ser editado (report_case.can_edit).

    O campo `order` foi preservado no update (não editável via formulário).
    """

    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"
    context_object_name = "obj"

    def get_queryset(self):
        """
        Limitou o acesso aos objetos vinculados a laudos do usuário autenticado.
        """
        return GenericExamObject.objects.filter(report_case__author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        """
        Impediu edição quando o laudo estiver bloqueado para alterações.
        """
        obj = self.get_object()
        if not obj.report_case.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Preservou `order` no update (caso exista auto-assign no model.save()).
        """
        form.instance.order = self.get_object().order
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirecionou para a página de detalhe do laudo após salvar.
        """
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )


class GenericExamObjectDeleteView(LoginRequiredMixin, DeleteView):
    """
    Excluiu um objeto genérico, respeitando:
    - acesso restrito ao autor do laudo;
    - bloqueio quando o laudo não puder ser editado (report_case.can_edit).
    """

    model = GenericExamObject
    template_name = "report_maker/generic_object_confirm_delete.html"
    context_object_name = "obj"

    def get_queryset(self):
        """
        Limitou o acesso aos objetos vinculados a laudos do usuário autenticado.
        """
        return GenericExamObject.objects.filter(report_case__author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        """
        Impediu exclusão quando o laudo estiver bloqueado para alterações.
        """
        obj = self.get_object()
        if not obj.report_case.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """
        Redirecionou para a página de detalhe do laudo após excluir.
        """
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )




class GenericExamObjectDetailView(
    ExamObjectMetaContextMixin,
    LoginRequiredMixin,
    DetailView,
):
    model = GenericExamObject
    template_name = "report_maker/generic_object_detail.html"
    context_object_name = "obj"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(report_case__author=self.request.user)
        )




@login_required
@require_POST
@csrf_protect
def generic_object_reorder(request, pk):
    """
    Reordenou objetos de exame de um laudo, com base na lista ordenada de UUIDs.

    Payload esperado:
      {"ordered_ids": ["uuid1", "uuid2", ...]}

    Regras:
    - somente autor do laudo
    - somente quando report.can_edit == True
    - reatribuiu order sequencialmente (1..N) na ordem recebida
    """
    report = ReportCase.objects.filter(pk=pk, author=request.user).first()
    if not report:
        raise Http404
    if not report.can_edit:
        raise Http404

    try:
        data = json.loads(request.body.decode("utf-8"))
        ordered_ids = data.get("ordered_ids", [])
        if not isinstance(ordered_ids, list) or not ordered_ids:
            return JsonResponse({"ok": False, "error": "ordered_ids inválido"}, status=400)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    # Garantiu que os IDs pertencem ao laudo
    qs = GenericExamObject.objects.filter(report_case=report, pk__in=ordered_ids)
    if qs.count() != len(ordered_ids):
        return JsonResponse({"ok": False, "error": "IDs não pertencem ao laudo"}, status=400)

    with transaction.atomic():
        # Atualizou em sequência (1..N) respeitando a ordem do cliente
        for idx, obj_id in enumerate(ordered_ids, start=1):
            GenericExamObject.objects.filter(report_case=report, pk=obj_id).update(order=idx)

    return JsonResponse({"ok": True})
