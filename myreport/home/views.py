from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse

from social_net.models import Post





class IndexView(TemplateView):
    template_name = "home/index.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("home:dashboard"))
        return super().dispatch(request, *args, **kwargs)




class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Página inicial do usuário autenticado.

    Exibe informações de boas-vindas e um resumo (preview) das postagens
    excluídas do próprio usuário, limitadas às 5 mais recentes, ordenadas
    por data de atualização.
    """
    template_name = "home/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["excluded_posts"] = (
            Post.objects.filter(user=self.request.user, is_active=False)
            .order_by("-updated_at")[:5]
        )

        return ctx




class ZenDoLaudoView(LoginRequiredMixin, TemplateView):
    """
    Com base no zen do python.
    """
    template_name = "home/zen_do_laudo.html"