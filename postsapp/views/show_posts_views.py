# postsapp/views/show_posts_views.py

from django.shortcuts import render
from postsapp.models import PostModel
from accountsapp.models import CustomUserModel
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required


from django.shortcuts import render
from postsapp.models import PostModel

def show_posts_view(request):
    user = request.user

    # Filtrar postagens que o usuário não ocultou
    posts = PostModel.objects.exclude(hidden_by_users=user)

    context = {
        'posts': posts,
        'user': user,
    }
    return render(request, 'show_posts.html', context)




@login_required
def hide_post(request, post_id):
    """
    Adiciona um post à lista de posts ocultos do usuário logado.
    """
    post = get_object_or_404(PostModel, id=post_id)
    if post not in request.user.hidden_posts.all():
        request.user.hidden_posts.add(post)
    return redirect('show_posts')  # Substitua 'feed' pela URL da página de onde o usuário veio
