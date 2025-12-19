# social_net/views.py
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Prefetch,Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, DetailView

from .forms import PostCommentForm, PostForm
from .models import Post, PostComment, PostLike, PostRating


class PostListView(LoginRequiredMixin, ListView):
    """
    Lista postagens ativas com paginação e busca por título.

    Anota no queryset se o usuário autenticado já curtiu e/ou avaliou cada postagem.
    Também pré-carrega comentários (nível raiz) e expõe os 5 mais recentes em
    `post.last_comments` para renderização direta no template.
    """

    model = Post
    template_name = "social_net/post_list.html"
    context_object_name = "posts"
    paginate_by = 10
    ordering = ["-updated_at"]

    def get_queryset(self):
        user = self.request.user

        comments_qs = (
            PostComment.objects.filter(is_active=True, parent__isnull=True)
            .select_related("user")
            .order_by("-created_at")
        )

        # Subquery para obter o valor da avaliação (value) do usuário logado para a Postagem atual
        user_rating_value_sq = PostRating.objects.filter(
            post_id=OuterRef("pk"), user_id=user.pk
        ).values("value")[:1]

        qs = (
            Post.objects.filter(is_active=True)
            .select_related("user")
            .annotate(
                has_liked=Exists(
                    PostLike.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
                ),
                has_rated=Exists(
                    PostRating.objects.filter(post_id=OuterRef("pk"), user_id=user.pk)
                ),
                # NOVO: Anota o valor da avaliação do usuário logado (pode ser NULL/None se não avaliou)
                user_rating_value=Subquery(user_rating_value_sq),
            )
            .prefetch_related(Prefetch("comments", queryset=comments_qs))
            .order_by("-updated_at")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(title__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        posts = ctx["posts"]
        for post in posts:
            post.last_comments = list(post.comments.all())[:5]

        ctx["form"] = PostForm()
        ctx["rating_range"] = range(1, 6)
        ctx["stars_5"] = range(1, 6)
        return ctx


# social_net/views.py

class PostDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe o detalhe de uma postagem específica, incluindo seu conteúdo completo
    e a listagem de todos os comentários associados.

    A view atua como ponto canônico da postagem, podendo ser acessada a partir
    do feed geral, da página pessoal do autor ou por link direto. Apenas postagens
    ativas são exibidas.

    Os comentários são recuperados em ordem cronológica crescente e acompanhados
    de um formulário para inserção de novos comentários.
    """
    model = Post
    template_name = "social_net/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return (
            Post.objects
            .filter(is_active=True)
            .select_related("user")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["comments"] = (
            PostComment.objects
            .filter(post=self.object, is_active=True)
            .select_related("user")
            .order_by("created_at")
        )

        ctx["comment_form"] = PostCommentForm()

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

    def form_valid(self, form):
        post = form.save(commit=False)
        post.user = self.request.user
        post.save()

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            post.has_liked = False
            post.has_rated = False
            post.last_comments = []
            html = render_to_string(
                "social_net/partials/post_item.html",
                {"post": post},
                request=self.request,
            )
            return JsonResponse({"success": True, "html": html})

        return super().form_valid(form)

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
