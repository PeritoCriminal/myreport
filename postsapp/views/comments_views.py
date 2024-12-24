# postsapp/views/comments_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from postsapp.forms import CommentForm
from postsapp.models import CommentsModel, PostModel


@login_required
def create_comment(request, post_id):
    post = get_object_or_404(PostModel, id=post_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')  # Caso o usuário envie uma imagem
        
        # Criar o comentário com o autor sendo o usuário logado
        comment = CommentsModel(
            author=request.user,  # Aqui está sendo atribuído o autor correto
            post=post,
            content=content,
            image=image
        )
        comment.save()
        
        return redirect('show_posts')  # Redireciona após salvar o comentário
    
    return redirect('show_posts')  # Redireciona caso a requisição não seja POST


@login_required
def edit_comment(request, comment_id):
    """
    Edita um comentário existente.
    """
    comment = get_object_or_404(CommentsModel, id=comment_id)
    
    if comment.author != request.user:
        return JsonResponse({'error': 'Você não tem permissão para editar este comentário'}, status=403)

    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('show_posts')  # Redireciona após editar o comentário
    else:
        form = CommentForm(instance=comment)

    return render(request, 'comment_form.html', {'form': form, 'comment': comment})

@login_required
def delete_comment(request, comment_id):
    """
    Exclui um comentário existente.
    """
    comment = get_object_or_404(CommentsModel, id=comment_id)
    if comment.author != request.user:
        return JsonResponse({'error': 'Você não tem permissão para excluir este comentário'}, status=403)

    comment.delete()
    return redirect('show_posts')  # Redireciona após excluir o comentário
