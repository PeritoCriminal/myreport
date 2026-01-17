# social_net/urls.py

from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,  # <- novo (CBV)
    PostCommentListView,
    PostCommentCreateView,
    ExcludedPostListView,
    ExcludedPostDetailView,
    HiddenPostListView,
    RestorePostView,
    post_rate,
    post_like,
    comment_delete,
    toggle_hide_post,
)

app_name = "social_net"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post_list"),
    path("post/<uuid:pk>/", PostDetailView.as_view(), name="post_detail"),
    path("posts/create/", PostCreateView.as_view(), name="post_create"),
    path("posts/<uuid:pk>/edit/", PostUpdateView.as_view(), name="post_update"),
    path("posts/<uuid:post_id>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("posts/<uuid:post_id>/rate/", post_rate, name="post_rate"),
    path("posts/<uuid:post_id>/like/", post_like, name="post_like"),
    path("posts/<uuid:post_id>/comments/", PostCommentListView.as_view(), name="comment_list"),
    path("posts/<uuid:post_id>/comments/create/", PostCommentCreateView.as_view(), name="comment_create"),
    path("comments/<uuid:comment_id>/delete/", comment_delete, name="comment_delete"),
    path("post/<uuid:post_id>/hide/", toggle_hide_post, name="post_hide_toggle"),
    path("posts/excluidas/", ExcludedPostListView.as_view(), name="excluded_post_list"),
    path("post/excluida/<uuid:pk>/restaurar/", RestorePostView.as_view(), name="post_restore"),
    path("posts/ocultadas/", HiddenPostListView.as_view(), name="hidden_post_list"),
]
