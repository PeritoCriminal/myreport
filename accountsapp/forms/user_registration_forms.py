# accounts/forms/user_registration_forms.py

from django import forms
from accountsapp.models.custom_user_model import CustomUserModel

class UserRegistrationForm(forms.ModelForm):
    """
    Formulário básico para registro de usuários.
    Contém o primeiro nome, o e-mail e o nome de usuário.
    """

    class Meta:
        model = CustomUserModel
        fields = ['username', 'first_name', 'email']

    def clean(self):
        """
        Garante que as validações do modelo sejam chamadas.
        """
        cleaned_data = super().clean()
        self.instance.username = cleaned_data.get('username')
        self.instance.first_name = cleaned_data.get('first_name')
        self.instance.email = cleaned_data.get('email')
        self.instance.clean()  # Chama as validações do modelo
        return cleaned_data



class CompleteRegistrationForm(forms.ModelForm):
    
    """
    Formulário para completar o cadastro do usuário após a confirmação do e-mail.
    Inclui os campos adicionais necessários para o registro completo.
    """

    class Meta:
        model = CustomUserModel
        fields = ['last_name', 'username', 'password']  # Inclua outros campos necessários

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput()

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("A senha deve ter pelo menos 8 caracteres.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
