# postsapp/views/post_views.py


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from postsapp.forms.post_forms import PostForm

@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # Define o autor como o usuário logado
            post.save()
            messages.success(request, 'Post criado com sucesso!')
            return redirect('home')  # Redireciona para a página inicial ou outra URL
        else:
            messages.error(request, 'Erro ao criar o post. Verifique os campos.')

    return render(request, 'create_post.html', {'form': form})

