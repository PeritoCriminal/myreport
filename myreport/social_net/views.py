# social_net/views.py
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from .forms import PostForm
from .models import Post, PostLike, PostRating


class PostListView(LoginRequiredMixin, ListView):
    """
    Exibe a lista paginada de postagens ativas, com suporte a busca por título
    e marcação no queryset indicando se o usuário autenticado já curtiu e/ou
    já avaliou cada postagem.
    """

    model = Post
    template_name = "social_net/post_list.html"
    context_object_name = "posts"
    paginate_by = 10
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

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
            )
            .order_by("-created_at")
        )

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = PostForm()
        ctx["rating_range"] = range(1, 6)
        ctx["stars_5"] = range(1, 6)
        return ctx


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Cria uma nova postagem para o usuário autenticado.
    Quando requisitado via AJAX, retorna HTML do item renderizado e sinaliza sucesso.
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
def post_like(request, post_id):
    """
    Alterna a curtida do usuário autenticado para a postagem informada e retorna JSON
    com o estado final e a contagem atualizada.
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
    Registra ou atualiza a avaliação (1 a 5) do usuário autenticado para a postagem
    informada e retorna JSON com o estado final.
    """

    post = get_object_or_404(Post, id=post_id, is_active=True)

    try:
        value = int(request.POST.get("value"))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "invalid_value"}, status=400)

    if value < 1 or value > 5:
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
