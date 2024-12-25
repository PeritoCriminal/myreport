


from django.contrib import admin
from .models.posts_models import PostModel
from .models.comments_models import CommentsModel

@admin.register(PostModel)
class PostModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')  # Campos exibidos na lista
    search_fields = ('title', 'content')  # Campos que podem ser buscados
    ordering = ('-created_at',)  # Ordem padrão (decrescente por data de criação)
    readonly_fields = ('created_at', 'updated_at')  # Campos apenas para leitura

@admin.register(CommentsModel)
class CommentModel(admin.ModelAdmin):
    list_display = ('id', 'post_id', 'author', 'post', 'created_at')  # Campos exibidos na lista
    search_fields = ('post', 'author')  # Campos que podem ser buscados
    ordering = ('-created_at',)  # Ordem padrão (decrescente por data de criação)
    readonly_fields = ('created_at', 'updated_at')  # Campos apenas para leitura

