


from django.contrib import admin
from .models.posts_models import PostModel

@admin.register(PostModel)
class PostModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')  # Campos exibidos na lista
    search_fields = ('title', 'content')  # Campos que podem ser buscados
    ordering = ('-created_at',)  # Ordem padrão (decrescente por data de criação)
    readonly_fields = ('created_at', 'updated_at')  # Campos apenas para leitura

