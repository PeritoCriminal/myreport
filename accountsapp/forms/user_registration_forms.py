# accounts/forms/user_registration_forms.py

from django import forms
from django.contrib.auth.hashers import make_password, check_password
from accountsapp.models.custom_user_model import CustomUserModel


class UserRegistrationForm(forms.ModelForm):
    """
    Formulário básico para registro de usuários.
    Contém o nome de usuário, e-mail, senha e confirmação de senha.
    """
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Senha"
    )
    password_confirmation = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirme a senha"
    )

    class Meta:
        model = CustomUserModel
        fields = ['username', 'email']

    def clean(self):
        """
        Garante que as validações do modelo sejam chamadas e valida as senhas.
        """
        cleaned_data = super().clean()

        # Validação das senhas
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')
        if password and password_confirmation and password != password_confirmation:
            self.add_error('password_confirmation', "As senhas não coincidem.")

        # Atribuir os dados validados ao modelo
        self.instance.username = cleaned_data.get('username')
        self.instance.email = cleaned_data.get('email')

        # Criptografar a senha antes de salvar
        if password:
            self.instance.password = make_password(password)

        # Chamar validações do modelo
        self.instance.clean()
        return cleaned_data

    def save(self, commit=True):
        """
        Salva o formulário, incluindo a senha criptografada.
        """
        user = super().save(commit=False)

        # Criptografar a senha antes de salvar
        if self.cleaned_data['password']:
            user.password = make_password(self.cleaned_data['password'])

        if commit:
            user.save()
        return user




class CompleteRegistrationForm(forms.ModelForm):
    """
    Formulário para completar o cadastro, validando a senha sem alterá-la.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(),
        label="Senha",
        help_text="Insira sua senha atual para confirmar as alterações."
    )

    class Meta:
        model = CustomUserModel
        fields = ['last_name', 'username']  # Inclua outros campos necessários

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Recebe o usuário na inicialização
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user or not check_password(password, self.user.password):
            raise forms.ValidationError("A senha está incorreta.")
        return password

    def save(self, commit=True):
        # Salva os campos atualizados, sem alterar a senha
        return super().save(commit=commit)

    


class UserLoginForm(forms.Form):
    """
    Formulário de login com username e senha.
    """
    username = forms.CharField(
        label="Nome de Usuário",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu nome de usuário'}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha'}),
    )
