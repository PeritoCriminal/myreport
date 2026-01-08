# report_maker/views/images.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from report_maker.models import ObjectImage


class _ImageAccessMixin(LoginRequiredMixin):
    """
    Mixin para resolver o objeto-alvo (content_object) e validar acesso:
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
    fields = ["image", "caption", "index"]

    def form_valid(self, form):
        ct, obj, _report = self._get_target_object()
        form.instance.content_type = ct
        form.instance.object_id = obj.pk
        return super().form_valid(form)

    def get_success_url(self):
        _ct, _obj, report = self._get_target_object()
        return reverse("report_maker:report_detail", kwargs={"pk": report.pk})


class ObjectImageUpdateView(LoginRequiredMixin, UpdateView):
    model = ObjectImage
    template_name = "report_maker/image_form.html"
    fields = ["image", "caption", "index"]
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


class ObjectImageDeleteView(LoginRequiredMixin, DeleteView):
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
