# social_net/views.py
from __future__ import annotations

# ─────────────────────────────────────
# Django
# ─────────────────────────────────────
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.files import File
from django.db.models import (
    Case,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
    When,
)
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

# ─────────────────────────────────────
# Apps do projeto
# ─────────────────────────────────────
from accounts.models import UserFollow
from groups.models import GroupMembership
from social_net.forms import PostForm, PostCommentForm
from social_net.models import (
    Post,
    PostComment,
    PostHidden,
    PostLike,
    PostRating,
)

# ─────────────────────────────────────
# Mixins comuns
# ─────────────────────────────────────
from common.mixins import (
    OwnerOr404Mixin,
    EditNotOpenedByThirdPartyOr404Mixin,
    ActiveObjectRequiredMixin,
    BlockIfOpenedByThirdPartyMixin,
    OwnerRequiredMixin,
    SoftDeleteMixin,
    UserAssignMixin,
)

User = get_user_model()

class PostListView(LoginRequiredMixin, ListView):
    """
    Lista postagens ativas com paginação e busca por título.

    Prioriza postagens de usuários seguidos (no topo),
    mantendo ordenação por atualização, e exclui postagens
    ocultadas pelo usuário autenticado.
    """

    model = Post
    template_name = "social_net/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user

        # subquery: postagens ocultadas pelo usuário
        hidden_sq = PostHidden.objects.filter(
            post_id=OuterRef("pk"),
            user=user,
        )

        comments_qs = (
            PostComment.objects.filter(is_active=True, parent__isnull=True)
            .select_related("user")
            .order_by("-created_at")
        )

        user_groups_sq = GroupMembership.objects.filter(user_id=user.pk).values("group_id")

        user_rating_value_sq = (
            PostRating.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
            .values("value")[:1]
        )

        # subquery: verifica se o autor da postagem é seguido pelo usuário
        is_from_followed_user_sq = UserFollow.objects.filter(
            follower=user,
            following_id=OuterRef("user_id"),
            is_active=True,
        )

        qs = (
            Post.objects.filter(is_active=True)
            .filter(Q(group__isnull=True) | Q(group_id__in=user_groups_sq))
            .select_related("user", "group")
            .annotate(
                has_liked=Exists(
                    PostLike.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
                ),
                has_rated=Exists(
                    PostRating.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
                ),
                user_rating_value=Subquery(user_rating_value_sq),
                is_from_followed=Case(
                    When(Exists(is_from_followed_user_sq), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                is_hidden=Case(
                    When(Exists(hidden_sq), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            .filter(is_hidden=0)
            .prefetch_related(Prefetch("comments", queryset=comments_qs))
            .order_by("-is_from_followed", "-updated_at")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(title__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # o feed depende disso
        ctx["form"] = PostForm(user=self.request.user)
        ctx["rating_range"] = range(1, 6)
        ctx["stars_5"] = range(1, 6)

        # mantém last_comments usado no post_item.html
        for post in ctx["posts"]:
            post.last_comments = list(post.comments.all())[:5]

        # marca opened no list (apenas os exibidos na página)
        user = self.request.user
        page_obj = ctx.get("page_obj")
        page_posts = list(page_obj.object_list) if page_obj else list(ctx.get("object_list") or [])
        post_ids = [p.id for p in page_posts]

        if post_ids:
            now = timezone.now()
            (
                Post.objects.filter(id__in=post_ids, opened_by_third_party=False)
                .exclude(user_id=user.id)
                .update(opened_by_third_party=True, opened_by_third_party_at=now)
            )

        return ctx


class PostDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe o detalhe de uma postagem específica, com listagem de comentários e formulário.
    """

    model = Post
    template_name = "social_net/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        user = self.request.user

        user_rating_value_sq = (
            PostRating.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
            .values("value")[:1]
        )

        return (
            Post.objects.filter(is_active=True)
            .select_related("user")
            .annotate(
                has_liked=Exists(
                    PostLike.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
                ),
                has_rated=Exists(
                    PostRating.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
                ),
                user_rating_value=Subquery(user_rating_value_sq),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object

        comments_qs = (
            PostComment.objects.filter(post=post, is_active=True)
            .select_related("user")
            .order_by("created_at")
        )

        likes_count = PostLike.objects.filter(post=post).count()

        rating_rows = (
            PostRating.objects.filter(post=post)
            .values("value")
            .annotate(total=Count("id"))
        )

        rating_counts = {i: 0 for i in range(1, 6)}
        for row in rating_rows:
            rating_counts[int(row["value"])] = int(row["total"])

        rating_total = sum(rating_counts.values())
        rating_sum = sum(star * qty for star, qty in rating_counts.items())
        rating_avg = (rating_sum / rating_total) if rating_total else 0

        ctx["comments"] = comments_qs
        ctx["comments_count"] = comments_qs.count()
        ctx["comment_form"] = PostCommentForm()

        ctx["likes_count"] = likes_count
        ctx["rating_counts"] = rating_counts
        ctx["rating_total"] = rating_total
        ctx["rating_avg"] = rating_avg
        ctx["user_rating_value"] = post.user_rating_value

        ctx["stars_5"] = range(1, 6)

        return ctx


class PostCreateView(LoginRequiredMixin, UserAssignMixin, CreateView):
    """
    Cria uma nova postagem do usuário autenticado.

    Quando a requisição é AJAX, retorna JSON com o HTML do item renderizado
    para inserção dinâmica no feed.
    """

    model = Post
    form_class = PostForm
    success_url = reverse_lazy("social_net:post_list")

    user_field = "user"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        post = form.save(commit=False)
        # user vem do UserAssignMixin via form_valid; mas aqui ainda estamos com commit=False,
        # então aplicamos antes de salvar:
        if not getattr(post, self.user_field, None):
            setattr(post, self.user_field, self.request.user)

        post.related_url = (self.request.POST.get("related_url") or "").strip() or None

        # Regra: se escolheu grupo, precisa ser membro
        if post.group_id:
            is_member = GroupMembership.objects.filter(
                user_id=self.request.user.pk,
                group_id=post.group_id,
            ).exists()
            if not is_member:
                form.add_error("group", "Você não é membro deste grupo.")
                return self.form_invalid(form)

        # Se veio de "Compartilhar PDF" e o usuário não enviou arquivo, anexa o placeholder
        share = self.request.POST.get("share")
        uploaded = self.request.FILES.get("media")

        if share == "pdf" and not uploaded and not getattr(post, "media", None):
            static_path = finders.find("technical_repository/img/pdf.png")
            if static_path:
                with open(static_path, "rb") as f:
                    post.media.save("pdf.png", File(f), save=False)

        post.save()
        self.object = post

        if (self.request.headers.get("X-Requested-With") or "") == "XMLHttpRequest":
            post.has_liked = False
            post.has_rated = False
            post.last_comments = []
            post.user_rating_value = None

            html = render_to_string(
                "social_net/partials/post_item.html",
                {"post": post, "rating_range": range(1, 6), "stars_5": range(1, 6)},
                request=self.request,
            )
            return JsonResponse({"success": True, "html": html}, status=200)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if (self.request.headers.get("x-requested-with") or "") == "XMLHttpRequest":
            errors_html = render_to_string(
                "social_net/partials/post_form_errors.html",
                {"form": form},
                request=self.request,
            )
            return JsonResponse({"success": False, "errors_html": errors_html}, status=400)

        return super().form_invalid(form)




class PostUpdateView(
    LoginRequiredMixin,
    OwnerOr404Mixin,
    EditNotOpenedByThirdPartyOr404Mixin,
    UpdateView,
):
    model = Post
    form_class = PostForm
    template_name = "social_net/post_update.html"

    owner_field = "user"                 # OwnerOr404Mixin
    opened_flag_field = "opened_by_third_party"  # EditNotOpenedByThirdPartyOr404Mixin

    def get_queryset(self):
        # mantém só "ativo" aqui; owner é garantido pelo OwnerOr404Mixin
        return Post.objects.filter(is_active=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        post = form.save(commit=False)

        # mantém related_url vindo do hidden input
        post.related_url = (self.request.POST.get("related_url") or "").strip() or None

        # Regra: se escolheu grupo, precisa ser membro
        if post.group_id:
            is_member = GroupMembership.objects.filter(
                user_id=self.request.user.pk,
                group_id=post.group_id,
            ).exists()
            if not is_member:
                form.add_error("group", "Você não é membro deste grupo.")
                return self.form_invalid(form)

        post.save()
        self.object = post
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action_url"] = reverse("social_net:post_update", kwargs={"pk": self.object.pk})
        ctx["submit_label"] = "Salvar"
        ctx["is_edit"] = True
        return ctx

    def get_success_url(self):
        return reverse("social_net:post_list")


class PostDeleteView(
    LoginRequiredMixin,
    OwnerOr404Mixin,
    SingleObjectMixin,
    View,
):
    """
    Inativa uma postagem do usuário autenticado (soft delete).
    Retorna JSON para remoção do card no front.
    """

    model = Post
    owner_field = "user"
    pk_url_kwarg = "post_id"

    def get_queryset(self):
        return Post.objects.filter(is_active=True)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save(update_fields=["is_active"])
        return JsonResponse({"success": True, "post_id": str(self.object.id)})


@login_required
@require_POST
def post_like(request, post_id):
    """
    Alterna a curtida do usuário autenticado na postagem informada.
    Retorna JSON com o estado final (`liked`) e a contagem atualizada.
    """
    post = get_object_or_404(Post, id=post_id, is_active=True)
    like_qs = PostLike.objects.filter(post=post, user=request.user)

    if like_qs.exists():
        like_qs.delete()
        liked = False
    else:
        PostLike.objects.create(post=post, user=request.user)
        liked = True

    return JsonResponse({"success": True, "liked": liked, "likes_count": post.likes.count()})


@login_required
@require_POST
def post_rate(request, post_id):
    """
    Registra ou atualiza a avaliação (1 a 5) do usuário autenticado na postagem.
    Retorna JSON indicando sucesso e o valor aplicado.
    """
    post = get_object_or_404(Post, id=post_id, is_active=True)

    try:
        value = int(request.POST.get("value"))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "invalid_value"}, status=400)

    if not (1 <= value <= 5):
        return JsonResponse({"success": False, "error": "out_of_range"}, status=400)

    PostRating.objects.update_or_create(
        post=post,
        user=request.user,
        defaults={"value": value},
    )

    return JsonResponse({"success": True, "rated": True, "rating_value": value})


class PostCommentListView(LoginRequiredMixin, ListView):
    """
    Lista comentários (nível raiz) de uma postagem, ordenados por data de criação.
    Esta view serve para renderização parcial (HTML) quando necessário.
    """

    model = PostComment
    template_name = "social_net/partials/comment_list.html"
    context_object_name = "comments"

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"], is_active=True)
        return (
            PostComment.objects.filter(post=post, is_active=True, parent__isnull=True)
            .select_related("user")
            .prefetch_related("replies__user")
            .order_by("created_at")
        )


class PostCommentCreateView(LoginRequiredMixin, CreateView):
    """
    Cria comentário em uma postagem, com suporte a resposta encadeada (parent).
    Quando a requisição é AJAX, retorna JSON com o HTML do comentário renderizado.
    """

    model = PostComment
    form_class = PostCommentForm

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs["post_id"], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.post = self.post_obj
        form.instance.user = self.request.user
        response = super().form_valid(form)

        if (self.request.headers.get("X-Requested-With") or "") == "XMLHttpRequest":
            html = render_to_string(
                "social_net/partials/comment_item.html",
                {"comment": self.object, "user": self.request.user},
                request=self.request,
            )
            return JsonResponse({"success": True, "html": html}, status=200)

        return response

    def form_invalid(self, form):
        if (self.request.headers.get("X-Requested-With") or "") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("social_net:post_detail", kwargs={"pk": self.post_obj.pk})


@login_required
@require_POST
def comment_delete(request, comment_id):
    """
    Inativa (soft delete) um comentário do usuário autenticado.
    Retorna JSON para remoção do comentário no front-end.
    """
    comment = get_object_or_404(PostComment, id=comment_id, is_active=True)

    if comment.user_id != request.user.id:
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)

    comment.is_active = False
    comment.save(update_fields=["is_active"])

    return JsonResponse({"success": True, "comment_id": str(comment.id)})


@require_POST
@login_required
def toggle_hide_post(request, post_id):
    """
    Alterna o estado de ocultação de uma postagem para o usuário autenticado.

    - Se a chamada for AJAX (fetch), retorna JSON.
    - Se for POST normal (form), redireciona para a página anterior
      (ou fallback no feed/lista).
    """
    post = get_object_or_404(Post, pk=post_id)

    obj, created = PostHidden.objects.get_or_create(post=post, user=request.user)

    hidden = True
    if not created:
        obj.delete()
        hidden = False

    wants_json = (request.headers.get("X-Requested-With") or request.headers.get("x-requested-with")) == "XMLHttpRequest"

    if wants_json:
        return JsonResponse({"hidden": hidden})

    return redirect(request.META.get("HTTP_REFERER") or reverse("social_net:post_list"))


class ExcludedPostListView(LoginRequiredMixin, ListView):
    """
    Lista as postagens excluídas (inativas) do usuário autenticado.
    """
    model = Post
    template_name = "social_net/excluded_post_list.html"
    context_object_name = "posts"
    paginate_by = 20

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user, is_active=False).order_by("-updated_at")


class ExcludedPostDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe uma postagem excluída (inativa) do próprio usuário, em modo de consulta.
    """
    model = Post
    template_name = "social_net/excluded_post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user, is_active=False)


class RestorePostView(LoginRequiredMixin, View):
    """
    Restaura uma postagem excluída do próprio usuário.
    """

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, user=request.user, is_active=False)
        post.is_active = True
        post.save(update_fields=["is_active"])
        return redirect(reverse("social_net:post_detail", args=[post.pk]))


class HiddenPostListView(LoginRequiredMixin, ListView):
    """
    Lista as postagens ocultadas pelo usuário autenticado.
    """
    model = Post
    template_name = "social_net/hidden_post_list.html"
    context_object_name = "posts"
    paginate_by = 20

    def get_queryset(self):
        hidden_post_ids = PostHidden.objects.filter(user=self.request.user).values("post_id")
        return (
            Post.objects.filter(id__in=Subquery(hidden_post_ids), is_active=True)
            .select_related("user", "group")
            .order_by("-updated_at")
        )


@login_required
@require_POST
def friendship(request, user_id: int):
    """
    Placeholder para ação de amizade/seguir.

    Objetivo imediato: evitar NoReverseMatch no template.
    Futuro: implementar criar/remover relação (friend request / follow etc.)
    """
    if request.user.id == user_id:
        raise Http404()

    get_object_or_404(User, pk=user_id, is_active=True)

    # TODO: implementar lógica real
    return redirect(request.META.get("HTTP_REFERER") or reverse("accounts:user_list"))