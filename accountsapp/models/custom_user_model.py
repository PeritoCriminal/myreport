# path = accountsapp/models/custom_user_model.py

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from PIL import Image
import os


class CustomUserModel(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        default='profile_pics/usercommonimg.jpg'
    )
    _original_profile_picture = None  # Atributo interno para rastrear a imagem original

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_profile_picture = self.profile_picture  # Armazena a imagem atual no momento da instância

    def clean(self):
        super().clean()
        self.validate_email_domain()

    def validate_email_domain(self):
        """
        Validação para restringir acesso a e-mails institucionais ativos.
        """
        valid_domains = [
            '@policiacientifica.sp.gov.br',
            '@policiacivil.sp.gov.br',
        ]
        if self.email and not any(self.email.endswith(domain) for domain in valid_domains):
            raise ValidationError({
                'email': "O e-mail deve pertencer aos domínios: "
                         "@policiacientifica.sp.gov.br ou @policiacivil.sp.gov.br."
            })

    def save(self, *args, **kwargs):
        """
        Redimensiona a imagem e deleta a anterior antes de salvar.
        """
        if self._original_profile_picture and self._original_profile_picture != self.profile_picture:
            self.delete_old_image()  # Deleta a imagem antiga

        super().save(*args, **kwargs)  # Salva o objeto normalmente

        # Redimensiona a nova imagem para no máximo 500x500, mantendo a proporção
        if self.profile_picture and self.profile_picture.path != 'profile_pics/usercommonimg.jpg':
            try:
                image_path = self.profile_picture.path
                img = Image.open(image_path)

                # Redimensiona mantendo a proporção
                img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

                # Salva a imagem redimensionada
                img.save(image_path)
            except FileNotFoundError:
                # Se não encontrar a imagem, trata como uma nova imagem
                pass

                self._original_profile_picture = self.profile_picture  # Atualiza a referência da imagem atual

    def delete_old_image(self):
        """
        Deleta a imagem antiga do sistema de arquivos.
        """
        if self._original_profile_picture and self._original_profile_picture.name != 'profile_pics/usercommonimg.jpg':
            try:
                os.remove(self._original_profile_picture.path)
            except (FileNotFoundError, OSError):
                # Se a imagem não for encontrada ou erro ao remover, simplesmente passa
                pass

    def delete(self, *args, **kwargs):
        """
        Deleta a imagem ao excluir o usuário.
        """
        if self.profile_picture and self.profile_picture.name != 'profile_pics/usercommonimg.jpg':
            try:
                self.profile_picture.delete(save=False)
            except FileNotFoundError:
                # Se a imagem não for encontrada ao deletar, apenas ignora
                pass
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.username
