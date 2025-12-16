# social_net/urls.py

from django.urls import path
from .views import PostListView, PostCreateView

app_name = "social_net"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post_list"),
    path("posts/create/", PostCreateView.as_view(), name="post_create"),
]