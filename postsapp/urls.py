# postsapp/urls.py


from django.urls import path
from postsapp.views import create_post, show_posts_view

urlpatterns = [
    path('teste', create_post, name='create_post'),
    path('show_post', show_posts_view, name='show_posts'),
]