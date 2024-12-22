# postsapp/views/show_posts_views.py

from django.shortcuts import render
from postsapp.models import PostModel
from accountsapp.models import CustomUserModel


def show_posts_view(request):
    posts = PostModel.objects.all()
    user = request.user

    context = {
        'posts': posts,
        'user': user,
    }
    return render(request, 'show_posts.html', context)