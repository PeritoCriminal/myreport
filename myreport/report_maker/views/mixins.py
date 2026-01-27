# myreport/report_maker/views/mixins.py
from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from report_maker.models import ReportCase, ObjectImage


class ReportCaseOwnedMixin:
    """
    Carrega o ReportCase e garante que pertence ao usuário autenticado.
    Faz cache em self.report_case para evitar múltiplas queries quando vários mixins chamam get_report_case().
    """
    report_pk_url_kwarg = "report_pk"
    report_case: ReportCase | None = None

    def get_report_case(self) -> ReportCase:
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
    Bloqueia qualquer operação de escrita quando report_case.can_edit == False.
    """

    def dispatch(self, request, *args, **kwargs):
        report = self.get_report_case()
        if not getattr(report, "can_edit", False):
            raise PermissionDenied("Este laudo não pode ser editado no momento.")
        return super().dispatch(request, *args, **kwargs)


class ReportCaseContextMixin(ReportCaseOwnedMixin):
    """
    Padroniza o context:
    - report -> self.report_case
    - obj -> self.object (quando existir) ou None (create)
    - mode -> "create" | "update" (se útil no template)
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
    Garante que o objeto consultado pertence ao report_case da URL.
    Útil para impedir trocar pk e "puxar" objeto de outro laudo do mesmo autor.
    """
    report_case_field_name = "report_case"  # FK no model

    def get_object(self, queryset=None):
        self.get_report_case()
        obj = super().get_object(queryset=queryset)

        fk = getattr(obj, f"{self.report_case_field_name}_id", None)
        if fk != self.report_case.id:
            raise Http404("Objeto não pertence a este laudo.")
        return obj


class ExamObjectImagesContextMixin:
    image_create_url_name: str | None = "report_maker:image_add"  # ou "image_add"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        obj = getattr(self, "object", None)
        if not obj or not obj.pk:
            ctx["images"] = []
            return ctx

        # 1) Mesmo vínculo mais provável do reportcase_detail: FK exam_object
        qs = ObjectImage.objects.filter(exam_object=obj)

        # 2) Fallback: GFK (content_type + object_id)
        if not qs.exists():
            ct = ContentType.objects.get_for_model(obj.__class__)
            qs = ObjectImage.objects.filter(content_type=ct, object_id=obj.pk)

        ctx["images"] = qs.order_by("index", "created_at")

        # botão add (sua rota atual)
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
    Retorna para a URL de origem após operações (edit/delete/create) via ?next=.
    Se não houver next, usa um fallback seguro.
    """
    next_param = "next"
    fallback_url_name: str | None = None
    fallback_url_kwargs: dict[str, str] | None = None  # mapeia nome_kwarg_url -> nome_kwarg_view

    def get_next_url(self) -> str | None:
        return (
            self.request.POST.get(self.next_param)
            or self.request.GET.get(self.next_param)
        ) or None

    def get_fallback_url(self) -> str:
        """
        Fallback padrão quando não existe ?next=.
        A View pode definir fallback_url_name/kwargs.
        """
        if self.fallback_url_name:
            kwargs = {}
            if self.fallback_url_kwargs:
                for url_kw, view_kw in self.fallback_url_kwargs.items():
                    kwargs[url_kw] = self.kwargs.get(view_kw)
            return reverse(self.fallback_url_name, kwargs=kwargs)

        # fallback genérico: tenta voltar no histórico
        return self.request.META.get("HTTP_REFERER", "/")

    def get_success_url(self) -> str:
        nxt = self.get_next_url()
        if nxt:
            return nxt
        return self.get_fallback_url()

