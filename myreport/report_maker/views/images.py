# report_maker/views/images.py
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from PIL import Image

from accounts.mixins import CanEditReportsRequiredMixin

from report_maker.forms import ObjectImageForm
from report_maker.models import ObjectImage
from report_maker.views.mixins import NextUrlMixin


class _ImageAccessMixin(LoginRequiredMixin, CanEditReportsRequiredMixin):
    """
    Resolve o objeto-alvo (content_object) e valida acesso:
    - objeto existe
    - é um ExamObject (ou herdeiro)
    - possui report_case
    - report_case pertence ao usuário
    - report_case está editável (can_edit)

    Também exige permissão efetiva do usuário para editar laudos
    (CanEditReportsRequiredMixin).

    Faz cache em self._target_cache.
    Retorno: (content_type, target_obj, report_case)
    """

    def _get_target_object(self):
        if getattr(self, "_target_cache", None) is not None:
            return self._target_cache

        app_label = self.kwargs.get("app_label")
        model = self.kwargs.get("model")
        object_id = self.kwargs.get("object_id")
        if not (app_label and model and object_id):
            raise Http404

        ct = ContentType.objects.filter(app_label=app_label, model=model).first()
        if not ct:
            raise Http404

        model_class = ct.model_class()
        if not model_class:
            raise Http404

        obj = model_class.objects.filter(pk=object_id).first()
        if not obj:
            raise Http404

        from report_maker.models import ExamObject  # import local para evitar circular

        if not isinstance(obj, ExamObject):
            raise Http404

        report = getattr(obj, "report_case", None)
        if not report:
            raise Http404

        if report.author_id != self.request.user.id:
            raise Http404
        if not getattr(report, "can_edit", False):
            raise Http404

        self._target_cache = (ct, obj, report)
        return self._target_cache

    def _validate_image_access(self, image: ObjectImage) -> ObjectImage:
        """
        Valida acesso para Update/Delete pelo próprio ObjectImage:
        - content_object existe
        - é ExamObject (ou herdeiro) + possui report_case
        - owner + can_edit
        """
        obj = image.content_object
        if not obj:
            raise Http404

        from report_maker.models import ExamObject  # import local para evitar circular

        if not isinstance(obj, ExamObject):
            raise Http404

        report = getattr(obj, "report_case", None)
        if not report:
            raise Http404

        if report.author_id != self.request.user.id:
            raise Http404
        if not getattr(report, "can_edit", False):
            raise Http404

        return image


# ─────────────────────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────────────────────
class ObjectImageCreateView(NextUrlMixin, _ImageAccessMixin, CreateView):
    model = ObjectImage
    template_name = "report_maker/image_form.html"
    form_class = ObjectImageForm  # index não é editável pelo usuário

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mode"] = "create"
        ctx["initial_image_url"] = ""

        _ct, _obj, report = self._get_target_object()
        ctx["cancel_url"] = self.get_next_url() or reverse(
            "report_maker:reportcase_detail",
            kwargs={"pk": report.pk},
        )
        return ctx

    def form_valid(self, form):
        ct, obj, _report = self._get_target_object()

        # vincula o GenericForeignKey ANTES de salvar
        form.instance.content_type = ct
        form.instance.object_id = obj.pk

        # dimensões originais da imagem
        uploaded = form.cleaned_data.get("image")
        if uploaded:
            with Image.open(uploaded) as im:
                form.instance.original_width, form.instance.original_height = im.size

        # index é calculado automaticamente no model (save)
        return super().form_valid(form)

    def get_fallback_url(self) -> str:
        _ct, _obj, report = self._get_target_object()
        return reverse("report_maker:reportcase_detail", kwargs={"pk": report.pk})


# ─────────────────────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────────────────────
class ObjectImageUpdateView(NextUrlMixin, _ImageAccessMixin, UpdateView):
    model = ObjectImage
    template_name = "report_maker/image_form.html"
    form_class = ObjectImageForm
    context_object_name = "image"

    def get_object(self, queryset=None):
        image = super().get_object(queryset=queryset)
        return self._validate_image_access(image)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mode"] = "update"

        img = self.object
        ctx["initial_image_url"] = img.image.url if getattr(img, "image", None) else ""

        report = img.content_object.report_case
        ctx["cancel_url"] = self.get_next_url() or reverse(
            "report_maker:reportcase_detail",
            kwargs={"pk": report.pk},
        )
        return ctx

    def form_valid(self, form):
        # garante que o index não seja alterado
        current = self.get_object()
        form.instance.index = current.index
        return super().form_valid(form)

    def get_fallback_url(self) -> str:
        obj = self.object.content_object
        return reverse("report_maker:reportcase_detail", kwargs={"pk": obj.report_case.pk})


# ─────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────
class ObjectImageDeleteView(NextUrlMixin, _ImageAccessMixin, DeleteView):
    model = ObjectImage
    template_name = "report_maker/image_confirm_delete.html"
    context_object_name = "image"

    def get_object(self, queryset=None):
        image = super().get_object(queryset=queryset)
        return self._validate_image_access(image)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        img = self.object
        report = img.content_object.report_case
        ctx["cancel_url"] = self.get_next_url() or reverse(
            "report_maker:reportcase_detail",
            kwargs={"pk": report.pk},
        )
        return ctx

    def get_fallback_url(self) -> str:
        obj = self.object.content_object
        return reverse("report_maker:reportcase_detail", kwargs={"pk": obj.report_case.pk})


# ─────────────────────────────────────────────────────────────
# Reorder (function-based)
# ─────────────────────────────────────────────────────────────
@login_required
@require_POST
def images_reorder(request):
    # ✅ permissão efetiva do usuário (validade/vínculo)
    if not request.user.can_edit_reports_effective:
        return HttpResponseForbidden("Sem permissão")

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        ordered_ids = data.get("ordered_ids", [])
        if not ordered_ids:
            return HttpResponseBadRequest("ordered_ids vazio")
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    qs = ObjectImage.objects.filter(pk__in=ordered_ids)
    if qs.count() != len(ordered_ids):
        return HttpResponseBadRequest("Há IDs inexistentes em ordered_ids")

    # usa o 1º id enviado para determinar o grupo (mais previsível que qs.first())
    first = ObjectImage.objects.filter(pk=ordered_ids[0]).first()
    if not first:
        return HttpResponseBadRequest("Imagens não encontradas")

    group_qs = ObjectImage.objects.filter(
        content_type_id=first.content_type_id,
        object_id=first.object_id,
    )

    if group_qs.count() != len(ordered_ids):
        return HttpResponseBadRequest("Imagens não pertencem ao mesmo objeto")

    obj = first.content_object
    report = getattr(obj, "report_case", None)
    if not report or report.author_id != request.user.id or not getattr(report, "can_edit", False):
        return HttpResponseForbidden("Sem permissão")

    ordered_ids_str = [str(x) for x in ordered_ids]

    with transaction.atomic():
        locked = list(group_qs.select_for_update().order_by("id"))

        tmp_base = 1_000_000
        for i, img in enumerate(locked, start=1):
            img.index = tmp_base + i
            img.save(update_fields=["index"])

        img_map = {str(img.pk): img for img in locked}
        for idx, img_id in enumerate(ordered_ids_str, start=1):
            img = img_map.get(img_id)
            if img:
                img.index = idx
                img.save(update_fields=["index"])

    return JsonResponse({"ok": True})
