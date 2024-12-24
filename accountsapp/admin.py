


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUserModel

@admin.register(CustomUserModel)
class CustomUserAdmin(UserAdmin):
    """
    Administração customizada do modelo CustomUserModel.
    """

    # Define os campos exibidos na lista de usuários
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')  # Campos para busca
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')  # Filtros laterais
    ordering = ('-date_joined',)  # Ordenação decrescente por data de criação

    # Define os campos no formulário de edição
    fieldsets = (
        (None, {'fields': ('username', 'password')}),  # Seção sem título, apenas para campos de login
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),  # Dados pessoais do usuário
        ('Configurações', {'fields': ('dark_theme',)}),  # Configuração de tema (para o tema escuro)
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),  # Controle de permissões
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),  # Informações sobre o login e a criação da conta
    )


    # Define os campos no formulário de criação
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
