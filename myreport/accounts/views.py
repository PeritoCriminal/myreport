# accounts/views.py

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.urls.exceptions import NoReverseMatch
from django.views.generic import CreateView, UpdateView, TemplateView
from django.db.models import Q, Avg, Count, Exists, OuterRef, Subquery
from django.views.generic import ListView

from .forms import UserRegistrationForm, UserProfileEditForm, UserSetPasswordForm
from .models import User

from social_net.models import Post, PostLike, PostRating




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
        next_url = super().get_success_url()
        
        try:
            reverse(next_url) 
            return next_url
        except NoReverseMatch:
            return reverse("home:index")




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




class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/user_profile.html"

    def dispatch(self, request, *args, **kwargs):
        self.profile_user = get_object_or_404(User, pk=kwargs["user_id"], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def _get_active_tab(self) -> str:
        tab = (self.request.GET.get("tab") or "posts").strip().lower()
        allowed = {"profile", "posts", "articles", "groups"}
        return tab if tab in allowed else "posts"

    def _get_posts_queryset(self):
        viewer = self.request.user
        author = self.profile_user

        user_rating_value_sq = (
            PostRating.objects
            .filter(post_id=OuterRef("pk"), user_id=viewer.pk)
            .values("value")[:1]
        )

        return (
            Post.objects
            .filter(is_active=True, user=author)
            .select_related("user")
            .annotate(
                has_liked=Exists(
                    PostLike.objects.filter(post_id=OuterRef("pk"), user_id=viewer.pk)
                ),
                has_rated=Exists(
                    PostRating.objects.filter(post_id=OuterRef("pk"), user_id=viewer.pk)
                ),
                user_rating_value=Subquery(user_rating_value_sq),

                likes_count=Count("likes", distinct=True),
                rating_total=Count("ratings", distinct=True),
                rating_avg=Avg("ratings__value"),
            )
            .order_by("-created_at")
        )


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        active_tab = self._get_active_tab()
        ctx["active_tab"] = active_tab
        ctx["profile_user"] = self.profile_user
        ctx["stars_5"] = range(1, 6)

        if active_tab == "posts":
            ctx["posts"] = self._get_posts_queryset()

        # futuramente:
        # if active_tab == "articles": ctx["articles"] = ...
        # if active_tab == "groups": ctx["groups"] = ...

        return ctx
