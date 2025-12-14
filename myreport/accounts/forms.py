from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    """
    Serve para:
    - Cadastro (CreateView): mantém password1/password2 obrigatórios.
    - Edição (UpdateView): remove password1/password2 do form, e desabilita username.
      (senha deve ser tratada em view/form separado: SetPasswordForm/PasswordChangeForm)
    """

    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "email",
            "role",
            "profile_image",
            "background_image",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "background_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bootstrap nos campos de senha (quando existirem)
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({"class": "form-control"})
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({"class": "form-control"})

        # Detecta edição: quando existe instance com pk
        is_edit = bool(getattr(self.instance, "pk", None))

        if is_edit:
            # Para edição, a senha NÃO deve estar aqui (tratar separadamente)
            self.fields.pop("password1", None)
            self.fields.pop("password2", None)

            # Normalmente username não deve ser alterado
            if "username" in self.fields:
                self.fields["username"].disabled = True
                # opcional: deixa visualmente "readonly"
                self.fields["username"].widget.attrs.update({"readonly": True})

            # Opcional: no modo edição, file não é obrigatório
            if "profile_image" in self.fields:
                self.fields["profile_image"].required = False
            if "background_image" in self.fields:
                self.fields["background_image"].required = False

    def clean_username(self):
        """
        Garante que, em edição, não vai falhar por tentar 'mudar' username
        (campo disabled não deveria mudar, mas isso evita edge cases).
        """
        is_edit = bool(getattr(self.instance, "pk", None))
        if is_edit:
            return self.instance.username
        return self.cleaned_data["username"]


class UserSetPasswordForm(SetPasswordForm):
    """
    Form separado para edição de senha (use em outra view/template).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-control"})
