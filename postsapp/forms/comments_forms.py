# commentsapp/comments_forms.py


from django import forms
from postsapp.models import CommentsModel


class CommentForm(forms.ModelForm):
    class Meta:
        model = CommentsModel
        fields = ['content', 'image']  # Campos que o usuário vai preencher

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # O campo 'author' é preenchido automaticamente com o usuário logado na view
        self.fields['content'].widget.attrs.update({'class': 'form-control'})
        self.fields['image'].widget.attrs.update({'class': 'form-control-file'})

