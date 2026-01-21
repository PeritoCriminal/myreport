# accounts/views.py

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db.models import Avg, Count, Exists, OuterRef, Q, Subquery
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.urls.exceptions import NoReverseMatch
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, FormView, ListView, TemplateView, UpdateView

from institutions.models import Nucleus, Team
from social_net.models import Post, PostLike, PostRating

from .home_registry import get_fallback_home_url, get_home_url_for_user

from .forms import (
    LinkInstitutionForm,
    UserPreferencesForm,  # <-- ADICIONE no forms.py ou importe do forms_preferences.py
    UserProfileEditForm,
    UserRegistrationForm,
    UserSetPasswordForm,
)
from .models import User, UserFollow


# ─────────────────────────────────────
# Auth / Perfil
# ─────────────────────────────────────
class UserRegisterView(CreateView):
    """
    Cadastro de usuário.
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


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        # 1) respeita next (URL), se for seguro
        next_url = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url

        # 2) senão, manda para a home preferida do usuário (key -> url_name)
        user = self.request.user
        return get_home_url_for_user(user, getattr(user, "default_home", "")) or get_fallback_home_url(user)


def user_logout(request):
    """
    Faz logout do usuário e redireciona para a home.
    Aceita GET e POST.
    """
    logout(request)
    return redirect("home:index")


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileEditForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("home:index")

    def get_object(self, queryset=None):
        return self.request.user


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = UserSetPasswordForm
    success_url = reverse_lazy("accounts:profile_edit")


# ─────────────────────────────────────
# Preferências
# ─────────────────────────────────────
class UserPreferencesUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserPreferencesForm
    template_name = "accounts/preferences_form.html"
    success_url = reverse_lazy("accounts:preferences")

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["profile_user"] = self.request.user

        # captura origem (GET)
        ctx["next"] = self.request.GET.get("next") or self.request.META.get("HTTP_REFERER")
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)

        next_url = self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return redirect(next_url)

        return response




# ─────────────────────────────────────
# Diretório / Perfil público
# ─────────────────────────────────────
class AllUserListView(LoginRequiredMixin, ListView):
    """
    Diretório de usuários.
    """

    model = User
    template_name = "social_net/friendship.html"
    context_object_name = "users"
    paginate_by = 24

    def get_queryset(self):
        qs = (
            User.objects.filter(is_active=True)
            .exclude(id=self.request.user.id)
            .order_by("display_name", "username")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(display_name__icontains=q) | Q(username__icontains=q))

        return qs.annotate(
            is_following=Exists(
                UserFollow.objects.filter(
                    follower=self.request.user,
                    following_id=OuterRef("pk"),
                    is_active=True,
                )
            )
        )


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
            PostRating.objects.filter(post_id=OuterRef("pk"), user_id=viewer.pk)
            .values("value")[:1]
        )

        return (
            Post.objects.filter(is_active=True, user=author)
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

        ctx["is_me"] = viewer.pk == target.pk
        ctx["is_following"] = UserFollow.objects.filter(
            follower=viewer,
            following=target,
            is_active=True,
        ).exists()

        ctx["followers_count"] = UserFollow.objects.filter(
            following=target,
            is_active=True,
        ).count()

        ctx["following_count"] = UserFollow.objects.filter(
            follower=target,
            is_active=True,
        ).count()

        if active_tab == "posts":
            ctx["posts"] = self._get_posts_queryset()

        return ctx


# ─────────────────────────────────────
# Ações
# ─────────────────────────────────────
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

        # Bloqueia open-redirect: aceita apenas URL relativa/host permitido
        if next_url and not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = ""

        return redirect(
            next_url or reverse("accounts:user_profile", kwargs={"user_id": target.pk})
        )


class LinkInstitutionView(LoginRequiredMixin, FormView):
    template_name = "accounts/link_institution.html"
    form_class = LinkInstitutionForm
    success_url = reverse_lazy("accounts:link_institution")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: LinkInstitutionForm):
        form.save()
        messages.success(self.request, "Vínculo institucional atualizado.")
        return super().form_valid(form)


# ─────────────────────────────────────
# AJAX
# ─────────────────────────────────────
@login_required
@require_GET
def ajax_nuclei(request):
    institution_id = (request.GET.get("institution") or "").strip()
    if not institution_id:
        return JsonResponse({"results": []})

    qs = Nucleus.objects.filter(institution_id=institution_id).order_by("name")
    data = [{"id": str(n.pk), "name": str(n)} for n in qs]
    return JsonResponse({"results": data})


@login_required
@require_GET
def ajax_teams(request):
    nucleus_id = (request.GET.get("nucleus") or "").strip()
    if not nucleus_id:
        return JsonResponse({"results": []})

    qs = Team.objects.filter(nucleus_id=nucleus_id).order_by("name")
    data = [{"id": str(t.pk), "name": str(t)} for t in qs]
    return JsonResponse({"results": data})
