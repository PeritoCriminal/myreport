from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView

from report_maker.forms import GenericExamObjectForm
from report_maker.models import GenericExamObject, ReportCase




class GenericExamObjectCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um objeto genérico vinculado a um Laudo.
    """

    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.report = (
            ReportCase.objects.filter(
                pk=kwargs["report_id"],
                author=request.user,
            ).first()
        )
        if not self.report or not self.report.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.report_case = self.report
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("report_maker:report_detail", kwargs={"pk": self.report.pk})




class GenericExamObjectUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edita um objeto genérico, respeitando o bloqueio do Laudo.
    """

    model = GenericExamObject
    form_class = GenericExamObjectForm
    template_name = "report_maker/generic_object_form.html"
    context_object_name = "obj"

    def get_queryset(self):
        return GenericExamObject.objects.filter(report_case__author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.report_case.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )




class GenericExamObjectDeleteView(LoginRequiredMixin, DeleteView):
    """
    Exclui um objeto genérico, respeitando o bloqueio do Laudo.
    """

    model = GenericExamObject
    template_name = "report_maker/generic_object_confirm_delete.html"
    context_object_name = "obj"

    def get_queryset(self):
        return GenericExamObject.objects.filter(report_case__author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.report_case.can_edit:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "report_maker:report_detail",
            kwargs={"pk": self.object.report_case_id},
        )




class GenericExamObjectDetailView(LoginRequiredMixin, DetailView):
    model = GenericExamObject
    template_name = "report_maker/generic_object_detail.html"
    context_object_name = "obj"

    def get_queryset(self):
        return GenericExamObject.objects.filter(report_case__author=self.request.user)
