# social_net/urls.py

from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostCommentListView,
    PostCommentCreateView,
    post_delete,
    post_rate,
    post_like,
)

app_name = "social_net"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post_list"),
    path("post/<uuid:pk>/", PostDetailView.as_view(), name="post_detail"),
    path("posts/create/", PostCreateView.as_view(), name="post_create"),
    path("posts/<uuid:post_id>/delete/", post_delete, name="post_delete"),
    path("posts/<uuid:post_id>/rate/", post_rate, name="post_rate"),
    path("posts/<uuid:post_id>/like/", post_like, name="post_like"),
    path("posts/<uuid:post_id>/comments/", PostCommentListView.as_view(), name="comment_list"),
    path("posts/<uuid:post_id>/comments/create/", PostCommentCreateView.as_view(), name="comment_create"),
]
