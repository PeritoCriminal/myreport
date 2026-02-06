# myreport/report_maker/views/mixins.py
from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse

from report_maker.models import ObjectImage, ReportCase


class ReportCaseOwnedMixin:
    """
    Resolve o ReportCase a partir do pk informado na URL e valida propriedade.

    Finalidade:
    - Centralizar a lógica de carregamento do laudo para views que operam “dentro” de um ReportCase
      (criação/edição/exclusão de objetos de exame, textos, etc.).
    - Garantir que o laudo pertence ao usuário autenticado (report.author == request.user).
    - Fazer cache em `self.report_case` para evitar múltiplas queries quando vários mixins e/ou a view
      chamarem `get_report_case()` mais de uma vez.

    Contrato:
    - A URL deve fornecer o pk do laudo em `report_pk_url_kwarg` (padrão: "report_pk").
    - A view (ou outro mixin) deve chamar `get_report_case()` quando precisar do laudo.
    """
    report_pk_url_kwarg = "report_pk"
    report_case: ReportCase | None = None

    def get_report_case(self) -> ReportCase:
        """
        Retorna o laudo resolvido da URL (com cache).

        Levanta:
        - Http404: se o parâmetro da URL não existir ou o laudo não for encontrado.
        - PermissionDenied: se o laudo não pertencer ao usuário atual.
        """
        if getattr(self, "report_case", None) is not None:
            return self.report_case  # type: ignore[return-value]

        pk = self.kwargs.get(self.report_pk_url_kwarg)
        if not pk:
            raise Http404("ReportCase não informado.")

        try:
            report = ReportCase.objects.select_related("author").get(pk=pk)
        except ReportCase.DoesNotExist:
            raise Http404("ReportCase não encontrado.")

        if report.author_id != self.request.user.id:
            raise PermissionDenied("Você não tem permissão para acessar este laudo.")

        self.report_case = report
        return report


class CanEditReportRequiredMixin(ReportCaseOwnedMixin):
    """
    Bloqueia operações de escrita quando o laudo não está editável.

    Regra aplicada:
    - resolve o laudo via `get_report_case()`;
    - exige `report.can_edit == True`.

    Observação importante:
    - este mixin valida o ESTADO DO LAUDO (domínio ReportCase).
    - a permissão “nível usuário” (assinatura/validade/vínculo) deve ser aplicada separadamente
      com `accounts.mixins.CanEditReportsRequiredMixin` nas views que alteram conteúdo.
    """

    def dispatch(self, request, *args, **kwargs):
        report = self.get_report_case()
        if not getattr(report, "can_edit", False):
            raise PermissionDenied("Este laudo não pode ser editado no momento.")
        return super().dispatch(request, *args, **kwargs)


class ReportCaseContextMixin(ReportCaseOwnedMixin):
    """
    Padroniza variáveis de template para views que operam dentro do laudo.

    Injeta no context:
    - report: o ReportCase resolvido
    - obj:    o objeto da view (self.object) quando existir, ou None (CreateView)
    - mode:   string opcional ("create" | "update") útil para templates reaproveitados

    Convenção:
    - Views podem definir `mode = "create"` ou `mode = "update"`.
    """
    mode: str | None = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.get_report_case()
        ctx["report"] = self.report_case

        # padrão "obj" em create/update
        ctx.setdefault("obj", getattr(self, "object", None))

        if self.mode:
            ctx["mode"] = self.mode
        return ctx


class ReportCaseObjectGuardMixin(ReportCaseOwnedMixin):
    """
    Impede “troca de pk” para acessar/alterar um objeto de outro laudo.

    Uso típico:
    - UpdateView/DeleteView de ExamObject:
        - a URL tem report_pk + pk do objeto
        - este mixin garante que o objeto realmente pertence ao report_case informado.

    Por que isso existe:
    - Mesmo com filtro por author, um usuário poderia tentar acessar um objeto de outro laudo dele
      (de outro report_pk) alterando o pk na URL. Isso pode quebrar invariantes no frontend e
      permitir edições em contexto errado.

    Implementação:
    - resolve o ReportCase via `get_report_case()`;
    - chama `super().get_object()`;
    - compara o FK do objeto (por padrão `report_case_id`) com `self.report_case.id`;
    - se não bater, retorna 404 (não revela existência do objeto).
    """
    report_case_field_name = "report_case"  # nome do FK no model

    def get_object(self, queryset=None):
        self.get_report_case()
        obj = super().get_object(queryset=queryset)

        fk = getattr(obj, f"{self.report_case_field_name}_id", None)
        if fk != self.report_case.id:
            raise Http404("Objeto não pertence a este laudo.")
        return obj


class ExamObjectImagesContextMixin:
    """
    Injeta a lista de imagens do objeto (ObjectImage) no context do template.

    Premissas:
    - A view expõe o objeto como `self.object` (padrão em UpdateView/DetailView).
    - ObjectImage usa GenericForeignKey (content_type + object_id).
    - Alguns objetos podem ter proxy/concrete; tentamos usar `obj.concrete` quando existir.

    Injeta no context:
    - images: queryset ordenado por (index, created_at)
    - image_create_url: URL para adicionar imagem ao objeto (opcional)

    Configuração:
    - image_create_url_name: nome da URL para "adicionar imagem" (default: "report_maker:image_add").
      Se None, não injeta `image_create_url`.
    """
    image_create_url_name: str | None = "report_maker:image_add"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        obj = getattr(self, "object", None)
        if not obj or not obj.pk:
            ctx["images"] = []
            return ctx

        # Alguns modelos expõem `concrete` (caso de herança/proxy). Se não existir, usa o próprio obj.
        concrete_obj = getattr(obj, "concrete", obj)
        ct = ContentType.objects.get_for_model(concrete_obj)

        ctx["images"] = (
            ObjectImage.objects.filter(content_type=ct, object_id=concrete_obj.pk)
            .order_by("index", "created_at")
        )

        if self.image_create_url_name:
            ctx["image_create_url"] = reverse(
                self.image_create_url_name,
                kwargs={
                    "app_label": obj._meta.app_label,
                    "model": obj._meta.model_name,
                    "object_id": obj.pk,
                },
            )
        return ctx


class NextUrlMixin:
    """
    Suporte a redirecionamento pós-operação usando ?next=.

    Objetivo:
    - Após Create/Update/Delete, retornar o usuário para a página “de origem”, quando ela for
      informada por querystring (?next=) ou por POST.

    Comportamento:
    1) Se existir `next` (GET ou POST), ela é usada como success_url.
    2) Caso contrário, usa um fallback:
       - se `fallback_url_name` estiver definido, faz reverse com kwargs mapeados
       - se não estiver, usa HTTP_REFERER (ou "/" como último recurso)

    Configuração:
    - next_param: nome do parâmetro (default: "next")
    - fallback_url_name: nome de URL para reverse (opcional)
    - fallback_url_kwargs: mapeamento {kwarg_da_url: kwarg_da_view} (opcional)
      Ex.: {"pk": "report_pk"} para pegar self.kwargs["report_pk"] e enviar como pk no reverse.
    """
    next_param = "next"
    fallback_url_name: str | None = None
    fallback_url_kwargs: dict[str, str] | None = None  # {url_kwarg: view_kwarg}

    def get_next_url(self) -> str | None:
        """Obtém a URL de retorno informada por GET/POST (?next=)."""
        return (
            self.request.POST.get(self.next_param)
            or self.request.GET.get(self.next_param)
        ) or None

    def get_fallback_url(self) -> str:
        """
        Retorna a URL de fallback quando não existe ?next=.

        Prioridade:
        1) reverse(fallback_url_name, kwargs=...)
        2) HTTP_REFERER
        3) "/"
        """
        if self.fallback_url_name:
            kwargs = {}
            if self.fallback_url_kwargs:
                for url_kw, view_kw in self.fallback_url_kwargs.items():
                    kwargs[url_kw] = self.kwargs.get(view_kw)
            return reverse(self.fallback_url_name, kwargs=kwargs)

        return self.request.META.get("HTTP_REFERER", "/")

    def get_success_url(self) -> str:
        """Define a URL final de redirecionamento (next > fallback)."""
        nxt = self.get_next_url()
        if nxt:
            return nxt
        return self.get_fallback_url()
