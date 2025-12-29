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
from django.http import HttpResponseBadRequest
from django.views import View

from .forms import UserRegistrationForm, UserProfileEditForm, UserSetPasswordForm
from .models import User, UserFollow

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
            return redirect("home:dashboard")
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
            return reverse("home:dashboard")




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
        
        qs = qs.annotate(
            is_following=Exists(
                UserFollow.objects.filter(
                    follower=self.request.user,
                    following_id=OuterRef("pk"),
                    is_active=True,
                )
            )
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

        viewer = self.request.user
        target = self.profile_user

        ctx["is_me"] = (viewer.pk == target.pk)
        ctx["is_following"] = UserFollow.objects.filter(
            follower=viewer,
            following=target,
            is_active=True,
        ).exists()

        # número de seguidores
        ctx["followers_count"] = UserFollow.objects.filter(
            following=target,
            is_active=True,
        ).count()

        # número de usuários que ele segue
        ctx["following_count"] = UserFollow.objects.filter(
            follower=target,
            is_active=True,
        ).count()


        if active_tab == "posts":
            ctx["posts"] = self._get_posts_queryset()

        return ctx




class FollowToggleView(LoginRequiredMixin, View):
    """
    Alterna seguir/deixar de seguir (soft toggle via is_active).
    """

    def post(self, request, user_id, *args, **kwargs):
        target = get_object_or_404(User, pk=user_id, is_active=True)

        if target.pk == request.user.pk:
            return HttpResponseBadRequest("Você não pode seguir a si mesmo.")

        rel, created = UserFollow.objects.get_or_create(
            follower=request.user,
            following=target,
            defaults={"is_active": True},
        )

        if not created:
            rel.is_active = not rel.is_active
            rel.save(update_fields=["is_active"])

        next_url = (request.POST.get("next") or "").strip()
        return redirect(next_url or reverse("accounts:user_profile", kwargs={"user_id": target.pk}))
