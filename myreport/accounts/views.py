# accounts/views.py

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.urls.exceptions import NoReverseMatch
from django.views.generic import CreateView, UpdateView
from django.db.models import Q
from django.views.generic import ListView

from .forms import UserRegistrationForm, UserProfileEditForm, UserSetPasswordForm
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

    def get_success_url(self):
        # respeita ?next=... quando existir
        next_url = self.get_redirect_url()
        if next_url:
            return next_url

        # tenta ir para a listagem de posts; se falhar, cai no home
        try:
            return reverse("social_net:post_list")
        except NoReverseMatch:
            return reverse("home:index")  # ajuste para o name real da sua home




def user_logout(request):
    """
    Faz logout do usuário e redireciona para a home.
    Aceita GET e POST.
    """
    logout(request)
    return redirect("home:index")




class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = UserSetPasswordForm
    success_url = reverse_lazy("accounts:profile_edit")  # ou home:index




class AllUserListView(LoginRequiredMixin, ListView):
    """
    Diretório de usuários para envio de solicitações de amizade.
    """
    model = User
    template_name = "social_net/friendship.html"
    context_object_name = "users"
    paginate_by = 24

    def get_queryset(self):
        qs = User.objects.exclude(id=self.request.user.id).order_by(
            "display_name", "username"
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(display_name__icontains=q) |
                Q(username__icontains=q)
            )
        return qs
