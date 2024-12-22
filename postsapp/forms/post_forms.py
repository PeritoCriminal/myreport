# postapp/forms/post_forms.py


from django import forms
from postsapp.models import PostModel

class PostForm(forms.ModelForm):
    class Meta:
        model = PostModel
        fields = ['title', 'image', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título do post',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escreva o conteúdo do post',
                'rows': 5,
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
            }),
        }
        labels = {
            'title': 'Título',
            'image': 'Imagem',
            'content': 'Conteúdo',
        }
        help_texts = {
            'image': 'Envie uma imagem que será ajustada automaticamente.',
        }