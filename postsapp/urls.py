# postsapp/urls.py


from django.urls import path
from postsapp.views import create_post, teste_view

urlpatterns = [
    path('teste', create_post, name='create_post'),
    path('testando', teste_view, name='teste'),
]