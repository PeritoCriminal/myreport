# postsapp/views/show_posts_views.py

from django.shortcuts import render
from postsapp.models import PostModel
from accountsapp.models import CustomUserModel
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


from django.shortcuts import render
from postsapp.models import PostModel, CommentsModel

def show_posts_view(request):
    user = request.user

    # Filtrar postagens que o usuário não ocultou
    posts = PostModel.objects.exclude(hidden_by_users=user)

    # Filtrar comentários de cada postagem
    comments = CommentsModel.objects.all()

    context = {
        'posts': posts,
        'comments': comments,
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
    return redirect('show_posts')



@login_required
def liked_post(request, post_id):
    """
    Adiciona ou remove um post da lista de likes do usuário logado.
    Retorna o número atualizado de curtidas.
    """
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = request.user
        post = get_object_or_404(PostModel, id=post_id)
        
        if post in user.liked_posts.all():
            user.liked_posts.remove(post)
            liked = False
        else:
            user.liked_posts.add(post)
            liked = True

        # Retorna o número atualizado de curtidas
        likes_count = post.liked_by_users.count()

        return JsonResponse({
            'likes_count': likes_count,
            'liked': liked,
        })
    else:
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    

@login_required
def liked_comment(request, comment_id):
    """
    Adiciona ou remove um comentário da lista de curtidas do usuário logado.
    Retorna o número atualizado de curtidas do comentário e o status de curtido.
    """
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = request.user
        comment = get_object_or_404(CommentsModel, id=comment_id)
        
        # Alterna entre curtir e descurtir
        if comment in user.liked_comments.all():
            user.liked_comments.remove(comment)
            liked = False
        else:
            user.liked_comments.add(comment)
            liked = True

        # Retorna o número atualizado de curtidas
        comment_likes_count = comment.commented_liked_by_users.count()

        return JsonResponse({
            'comment_likes_count': comment_likes_count,  # Número atualizado de curtidas
            'liked': liked,  # Status de curtido
        })
    else:
        return JsonResponse({'error': 'Requisição inválida'}, status=400)


@login_required
def toggle_comment_like(request, comment_id):
    comment = CommentsModel.objects.get(pk=comment_id)
    if request.user in comment.commented_liked_by_users.all():
        comment.commented_liked_by_users.remove(request.user)
    else:
        comment.commented_liked_by_users.add(request.user)
    likes_count = comment.commented_liked_by_users.count()
    return JsonResponse({'likes_count': likes_count})



def delete_comment_view(request, comment_id):
    if request.method == 'DELETE':
        comment = get_object_or_404(CommentsModel, id=comment_id)

        # Verifica se o usuário logado é o autor do comentário ou o autor do post
        if comment.author == request.user or comment.post.author == request.user:
            comment.delete()
            return JsonResponse({'message': 'Comentário deletado com sucesso!'}, status=200)
        else:
            return JsonResponse({'error': 'Você não tem permissão para deletar este comentário.'}, status=403)

    return JsonResponse({'error': 'Método não permitido.'}, status=405)