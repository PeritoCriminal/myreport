# social_net/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Post


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
