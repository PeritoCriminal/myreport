# postsapp/views/comment_views.py


from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from postsapp.models import CommentsModel, PostModel

@login_required
def save_comment(request):
    if request.method == 'POST':
        post_id = request.POST.get('post')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        # Validação e criação do comentário
        post = PostModel.objects.get(id=post_id)
        CommentsModel.objects.create(
            post=post,
            author=request.user,
            content=content,
            image=image
        )
        return redirect('show_posts')  # Redirecione para a página desejada
