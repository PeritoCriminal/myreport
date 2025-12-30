# social_net/views.py
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Prefetch, Subquery, Count, Q, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponseRedirect, request
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, DetailView

from .forms import PostCommentForm, PostForm
from .models import Post, PostComment, PostLike, PostRating, PostHidden
from groups.models import GroupMembership
from accounts.models import UserFollow




from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Q, Exists, OuterRef, Subquery,
    Case, When, Value, IntegerField, Prefetch
)
from django.views.generic import ListView

from accounts.models import UserFollow
from groups.models import GroupMembership
from social_net.models import (
    Post, PostComment, PostLike, PostRating, PostHidden
)
from social_net.forms import PostForm


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

        user_groups_sq = GroupMembership.objects.filter(
            user_id=user.pk
        ).values("group_id")

        user_rating_value_sq = (
            PostRating.objects.filter(
                post_id=OuterRef("pk"),
                user_id=user.pk
            )
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
            .filter(
                Q(group__isnull=True) |
                Q(group_id__in=user_groups_sq)
            )
            .select_related("user", "group")
            .annotate(
                # flags do usuário
                has_liked=Exists(
                    PostLike.objects.filter(
                        post_id=OuterRef("pk"),
                        user_id=user.pk
                    )
                ),
                has_rated=Exists(
                    PostRating.objects.filter(
                        post_id=OuterRef("pk"),
                        user_id=user.pk
                    )
                ),
                user_rating_value=Subquery(user_rating_value_sq),

                # flag: 1 = autor seguido | 0 = não seguido
                is_from_followed=Case(
                    When(
                        Exists(is_from_followed_user_sq),
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                ),

                # flag: 1 = ocultada | 0 = visível
                is_hidden=Case(
                    When(
                        Exists(hidden_sq),
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            # exclui ocultadas
            .filter(is_hidden=0)
            .prefetch_related(
                Prefetch("comments", queryset=comments_qs)
            )
            # primeiro seguidos, depois os demais; ambos por atualização
            .order_by("-is_from_followed", "-updated_at")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(title__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        for post in ctx["posts"]:
            post.last_comments = list(post.comments.all())[:5]

        ctx["form"] = PostForm(user=self.request.user)
        ctx["rating_range"] = range(1, 6)
        ctx["stars_5"] = range(1, 6)
        return ctx





class PostDetailView(LoginRequiredMixin, DetailView):
    """ 
    Exibe o detalhe de uma postagem específica, incluindo seu conteúdo completo 
    e a listagem de todos os comentários associados. A view atua como ponto canônico 
    da postagem, podendo ser acessada a partir do feed geral, da página pessoal do 
    autor ou por link direto. Apenas postagens ativas são exibidas. Os comentários 
    são recuperados em ordem cronológica crescente e acompanhados de um formulário 
    para inserção de novos comentários. 
    """
    model = Post
    template_name = "social_net/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        user = self.request.user

        # valor da avaliação do usuário logado para esta postagem (None se não existir)
        user_rating_value_sq = (
            PostRating.objects
            .filter(post_id=OuterRef("pk"), user_id=user.pk)
            .values("value")[:1]
        )

        return (
            Post.objects
            .filter(is_active=True)
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
            PostComment.objects
            .filter(post=post, is_active=True)
            .select_related("user")
            .order_by("created_at")
        )

        # Contagem total de curtidas (evita hits extras no template)
        likes_count = PostLike.objects.filter(post=post).count()

        # Contagem por estrelas (1..5) num único query
        # retorna algo como: [{'value': 5, 'total': 3}, {'value': 4, 'total': 1}, ...]
        rating_rows = (
            PostRating.objects
            .filter(post=post)
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

        # Curtidas
        ctx["likes_count"] = likes_count

        # Avaliações
        ctx["rating_counts"] = rating_counts          # dict: 1..5
        ctx["rating_total"] = rating_total            # total de avaliações
        ctx["rating_avg"] = rating_avg                # média (0 se não houver)
        ctx["user_rating_value"] = post.user_rating_value  # 1..5 ou None

        # Se você usa no template para desenhar estrelas
        ctx["stars_5"] = range(1, 6)

        return ctx




class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Cria uma nova postagem do usuário autenticado.

    Quando a requisição é AJAX, retorna JSON com o HTML do item renderizado
    para inserção dinâmica no feed.
    """

    model = Post
    form_class = PostForm
    success_url = reverse_lazy("social_net:post_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        post = form.save(commit=False)
        post.user = self.request.user

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

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            post.has_liked = False
            post.has_rated = False
            post.last_comments = []
            post.user_rating_value = None

            html = render_to_string(
                "social_net/partials/post_item.html",
                {
                    "post": post,
                    "rating_range": range(1, 6),
                    "stars_5": range(1, 6),
                },
                request=self.request,  # garante `request` no template
            )
            return JsonResponse({"success": True, "html": html}, status=200)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            errors_html = render_to_string(
                "social_net/partials/post_form_errors.html",
                {"form": form},
                request=self.request,
            )
            return JsonResponse({"success": False, "errors_html": errors_html}, status=400)

        return super().form_invalid(form)





@login_required
@require_POST
def post_delete(request, post_id):
    """
    Inativa uma postagem do usuário autenticado (soft delete).

    Retorna JSON para remoção do card no front.
    """
    post = get_object_or_404(Post, id=post_id, is_active=True)

    if post.user_id != request.user.id:
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)

    post.is_active = False
    post.save(update_fields=["is_active"])

    return JsonResponse({"success": True, "post_id": str(post.id)})




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

    return JsonResponse(
        {
            "success": True,
            "liked": liked,
            "likes_count": post.likes.count(),
        }
    )




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

    return JsonResponse(
        {
            "success": True,
            "rated": True,
            "rating_value": value,
        }
    )




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

    Quando a requisição é AJAX, retorna JSON com o HTML do comentário renderizado
    para inserção dinâmica na lista já exibida.
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

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html = render_to_string(
                "social_net/partials/comment_item.html",
                {"comment": self.object, "user": self.request.user},
                request=self.request,
            )
            return JsonResponse({"success": True, "html": html}, status=200)

        return response
    
    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("social_net:post_detail", kwargs={"pk": self.post_obj.pk})




# social_net/views.py

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

    return JsonResponse(
        {
            "success": True,
            "comment_id": str(comment.id),
        }
    )




@login_required
def toggle_hide_post(request, post_id):
    """
    Alterna o estado de ocultação de uma postagem para o usuário autenticado.

    Quando acionada, esta view verifica se a postagem informada já se encontra
    marcada como ocultada pelo usuário:
    – caso não esteja, cria o registro de ocultação, fazendo com que a postagem
      deixe de ser exibida em seu feed;
    – caso já esteja, remove o registro correspondente, tornando a postagem
      novamente visível.

    A operação não altera a postagem em si, não interfere em curtidas,
    comentários ou demais interações, e afeta exclusivamente a visualização
    do usuário autenticado.
    """
    post = get_object_or_404(Post, pk=post_id)

    obj, created = PostHidden.objects.get_or_create(
        post=post,
        user=request.user,
    )

    if not created:
        obj.delete()
        return JsonResponse({"hidden": False})

    return JsonResponse({"hidden": True})

