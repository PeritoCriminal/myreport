# social_net/urls.py

from django.urls import path
from .views import (
    PostListView,
    PostCreateView,
    post_rate,
    post_like,
)

app_name = "social_net"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post_list"),
    path("posts/create/", PostCreateView.as_view(), name="post_create"),
    path("posts/<uuid:post_id>/rate/", post_rate, name="post_rate"),
    path("posts/<uuid:post_id>/like/", post_like, name="post_like"),
]
