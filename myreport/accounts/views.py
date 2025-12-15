# accounts/views.py

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import UserRegistrationForm, UserProfileEditForm
from .models import User


class UserRegisterView(CreateView):
    """
    Cadastro de usuário
    """
    model = User
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        # Usuário logado não deve acessar cadastro
        if request.user.is_authenticated:
            return redirect("home:index")
        return super().dispatch(request, *args, **kwargs)


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileEditForm   # <-- AQUI
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("home:index")

    def get_object(self, queryset=None):
        return self.request.user
    


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def user_logout(request):
    """
    Faz logout do usuário e redireciona para a home.
    Aceita GET e POST.
    """
    logout(request)
    return redirect("home:index")


from .forms import UserSetPasswordForm


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = UserSetPasswordForm
    success_url = reverse_lazy("accounts:profile_edit")  # ou home:index
