# social_net/views.py
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Post
from .forms import PostForm


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "social_net/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return (
            Post.objects
            .filter(is_active=True)
            .select_related("user")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = PostForm()
        return ctx


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("social_net:post_list")

    def form_valid(self, form):
        post = form.save(commit=False)
        post.user = self.request.user
        post.save()

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
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
