from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView

from report_maker.models import ObjectImage, ReportCase


class ObjectImageCreateView(LoginRequiredMixin, CreateView):
    """
    Upload de imagem vinculada a um objeto de exame.
    """

    model = ObjectImage
    template_name = "report_maker/image_form.html"
    fields = ["image", "caption", "index"]

    def dispatch(self, request, *args, **kwargs):
        self.report = ReportCase.objects.filter(
            pk=kwargs["report_id"],
            author=request.user,
        ).first()
        if not self.report or not self.report.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        content_type = ContentType.objects.get(
            app_label=self.kwargs["app_label"],
            model=self.kwargs["model"],
        )

        form.instance.report_case = self.report
        form.instance.content_type = content_type
        form.instance.object_id = self.kwargs["object_id"]

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.report.pk},
        )


class ObjectImageDeleteView(LoginRequiredMixin, DeleteView):
    """
    Exclusão de imagem vinculada a objeto de exame.
    """

    model = ObjectImage
    template_name = "report_maker/image_confirm_delete.html"
    context_object_name = "image"

    def get_queryset(self):
        return ObjectImage.objects.filter(
            report_case__author=self.request.user,
            report_case__status=ReportCase.Status.OPEN,
        )

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )
