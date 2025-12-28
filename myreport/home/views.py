from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse





class IndexView(TemplateView):
    template_name = "home/index.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("home:dashboard"))
        return super().dispatch(request, *args, **kwargs)




class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Página inicial do usuário autenticado.
    """
    template_name = "home/dashboard.html"