from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin




class HomeView(TemplateView):
    """
    Página inicial do usuário não autenticado.
    """
    template_name = 'home/index.html'




class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Página inicial do usuário autenticado.
    """
    template_name = "home/dashboard.html"