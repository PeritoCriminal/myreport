# accounts/views.py

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import User
from .forms import UserRegistrationForm


class UserRegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        """
        Deixa o CreateView salvar o usuário (com senha),
        depois você pode fazer algo extra se quiser.
        """
        response = super().form_valid(form)
        # aqui daria para fazer login automático, enviar email etc.
        return response

    def dispatch(self, request, *args, **kwargs):
        """
        Opcional: se o usuário já estiver logado, não faz sentido
        mostrar tela de cadastro.
        """
        if request.user.is_authenticated:
            return redirect("home:index")  # ou outra página que você quiser
        return super().dispatch(request, *args, **kwargs)




from django.contrib.auth.views import LoginView


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

