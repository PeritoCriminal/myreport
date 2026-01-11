# report_maker/views/images.py
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from PIL import Image

from report_maker.forms import ObjectImageForm
from report_maker.models import ObjectImage


class _ImageAccessMixin(LoginRequiredMixin):
    """
    Resolve o objeto-alvo (content_object) e valida acesso:
    - objeto existe
    - possui report_case
    - report_case pertence ao usuário
    - report_case está editável (can_edit)
    """

    def _get_target_object(self):
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

        report = getattr(obj, "report_case", None)
        if not report:
            raise Http404
        if report.author_id != self.request.user.id:
            raise Http404
        if not getattr(report, "can_edit", False):
            raise Http404

        return ct, obj, report


class ObjectImageCreateView(_ImageAccessMixin, CreateView):
    model = ObjectImage
    template_name = "report_maker/image_form.html"
    form_class = ObjectImageForm  # index não é editável pelo usuário

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mode"] = "create"
        ctx["initial_image_url"] = ""

        _ct, _obj, report = self._get_target_object()
        ctx["cancel_url"] = reverse("report_maker:report_detail", kwargs={"pk": report.pk})
        return ctx

    def form_valid(self, form):
        ct, obj, _report = self._get_target_object()

        # vincula o GenericForeignKey ANTES de salvar
        form.instance.content_type = ct
        form.instance.object_id = obj.pk

        # dimensões originais
        uploaded = form.cleaned_data.get("image")
        if uploaded:
            with Image.open(uploaded) as im:
                form.instance.original_width, form.instance.original_height = im.size

        # index automático (max + 1) por objeto-alvo, com lock
        with transaction.atomic():
            qs = (
                ObjectImage.objects.select_for_update()
                .filter(content_type=ct, object_id=obj.pk)
            )
            last = qs.aggregate(m=Max("index"))["m"] or 0
            form.instance.index = last + 1
            return super().form_valid(form)

    def get_success_url(self):
        _ct, _obj, report = self._get_target_object()
        return reverse("report_maker:report_detail", kwargs={"pk": report.pk})


class ObjectImageUpdateView(_ImageAccessMixin, UpdateView):
    model = ObjectImage
    template_name = "report_maker/image_form.html"
    form_class = ObjectImageForm
    context_object_name = "image"

    def get_object(self, queryset=None):
        image = super().get_object(queryset=queryset)
        obj = image.content_object
        if not obj:
            raise Http404

        report = getattr(obj, "report_case", None)
        if not report:
            raise Http404
        if report.author_id != self.request.user.id:
            raise Http404
        if not getattr(report, "can_edit", False):
            raise Http404

        return image

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mode"] = "update"

        img = self.get_object()
        ctx["initial_image_url"] = img.image.url if getattr(img, "image", None) else ""

        obj = img.content_object
        report = obj.report_case
        ctx["cancel_url"] = reverse("report_maker:report_detail", kwargs={"pk": report.pk})
        return ctx

    def form_valid(self, form):
        # garante que o index não seja alterado
        form.instance.index = self.get_object().index
        return super().form_valid(form)

    def get_success_url(self):
        obj = self.object.content_object
        return reverse("report_maker:report_detail", kwargs={"pk": obj.report_case.pk})


class ObjectImageDeleteView(_ImageAccessMixin, DeleteView):
    model = ObjectImage
    template_name = "report_maker/image_confirm_delete.html"
    context_object_name = "image"

    def get_object(self, queryset=None):
        image = super().get_object(queryset=queryset)
        obj = image.content_object
        if not obj:
            raise Http404

        report = getattr(obj, "report_case", None)
        if not report:
            raise Http404
        if report.author_id != self.request.user.id:
            raise Http404
        if not getattr(report, "can_edit", False):
            raise Http404

        return image

    def get_success_url(self):
        obj = self.object.content_object
        return reverse("report_maker:report_detail", kwargs={"pk": obj.report_case.pk})


@login_required
@require_POST
def images_reorder(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        ordered_ids = data.get("ordered_ids", [])
        if not ordered_ids:
            return HttpResponseBadRequest("ordered_ids vazio")
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    qs = ObjectImage.objects.filter(pk__in=ordered_ids)
    first = qs.first()
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
    if (
        not report
        or report.author_id != request.user.id
        or not getattr(report, "can_edit", False)
    ):
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
