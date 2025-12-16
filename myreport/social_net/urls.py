# social_net/urls.py

from django.urls import path
from .views import PostListView

app_name = "social_net"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post_list"),
]