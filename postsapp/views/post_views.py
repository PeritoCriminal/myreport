# postsapp/views/post_views.py


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from postsapp.forms.post_forms import PostForm
from postsapp.models import PostModel


@login_required
def create_or_edit_post(request, post_id=None):
    # Busca o post existente ou inicializa um novo
    if post_id:
        post = get_object_or_404(PostModel, id=post_id)
        if post.author != request.user:
            messages.error(request, "Você não tem permissão para editar este post.")
            return redirect('show_posts')  # Redireciona para a página inicial
    else:
        post = PostModel(author=request.user)

    # Inicializa o formulário com os dados do post existente (ou novo)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if post_id:
                messages.success(request, 'Post atualizado com sucesso!')
            else:
                messages.success(request, 'Post criado com sucesso!')
            return redirect('show_posts')  # Redireciona para a página inicial ou outra URL
        else:
            messages.error(request, 'Erro ao salvar o post. Verifique os campos.')

    return render(request, 'create_post.html', {'form': form, 'post': post})



@login_required
def delete_post(request, post_id):
    post = get_object_or_404(PostModel, id=post_id)

    if post.author != request.user:
        messages.error(request, "Você não tem permissão para deletar este post.")
        return redirect('show_posts')  # Redireciona para a página inicial ou outra URL

    post.delete()
    messages.success(request, "Postagem deletada com sucesso!")
    return redirect('show_posts')  # Redireciona para a página inicial ou outra URL