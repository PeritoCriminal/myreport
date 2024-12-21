from django.test import TestCase
from accountsapp.models.custom_user_model import CustomUserModel
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
import os
from django.core.files.uploadedfile import SimpleUploadedFile


class CustomUserModelTest(TestCase):

    def setUp(self):
        """Configura o ambiente de testes para o usuário base."""
        self.valid_email = "usuario@policiacientifica.sp.gov.br"
        self.valid_username = "usuario"
        self.user = CustomUserModel.objects.create_user(
            username=self.valid_username,
            email=self.valid_email,
            password="senhaSegura123"
        )

    def test_nao_permitir_email_duplicado(self):
        """Testa que não é permitido cadastrar dois usuários com o mesmo email."""
        with self.assertRaises(IntegrityError):
            CustomUserModel.objects.create_user(
                username="outro_usuario",
                email=self.valid_email,
                password="senhaSegura123"
            )

    def test_nao_permitir_username_duplicado(self):
        """Testa que não é permitido cadastrar dois usuários com o mesmo username."""
        with self.assertRaises(IntegrityError):
            CustomUserModel.objects.create_user(
                username=self.valid_username,
                email="outro_email@policiacientifica.sp.gov.br",
                password="senhaSegura123"
            )

    def test_nao_permitir_email_fora_da_lista_de_dominios_validos(self):
        """Testa que emails fora da lista de domínios válidos não podem ser cadastrados."""
        invalid_email = "usuario@gmail.com"
        with self.assertRaises(ValidationError):
            user = CustomUserModel(
                username="novo_usuario",
                email=invalid_email
            )
            user.clean()  # Chama o método de validação explicitamente antes de salvar

    def test_permitir_email_com_dominio_valido(self):
        """Testa que emails dentro da lista de domínios válidos são permitidos."""
        valid_email = "novo_usuario@policiacivil.sp.gov.br"
        user = CustomUserModel(
            username="novo_usuario",
            email=valid_email
        )
        try:
            user.clean()  # Chama o método de validação explicitamente
        except ValidationError:
            self.fail("ValidationError foi levantado para um email válido.")

    def test_image_deleted_when_user_deleted(self):
        """Testa se a imagem é deletada ao excluir o usuário"""
        # Adiciona uma imagem ao usuário
        with open('path_to_image.jpg', 'rb') as img:
            image = SimpleUploadedFile('profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = image
            self.user.save()

        # Salva o caminho da imagem antes de deletar o usuário
        image_path = self.user.profile_picture.path
        
        # Deleta o usuário
        self.user.delete()

        # Verifica se a imagem foi deletada
        self.assertFalse(os.path.exists(image_path), f"A imagem {image_path} não foi deletada quando o usuário foi excluído.")

    def test_image_updated_and_old_image_deleted(self):
        """Testa se a imagem antiga é deletada ao alterar a imagem do usuário"""
        # Adiciona uma imagem inicial ao usuário
        with open('path_to_image.jpg', 'rb') as img:
            image = SimpleUploadedFile('profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = image
            self.user.save()

        # Salva o caminho da imagem antes de alterá-la
        old_image_path = self.user.profile_picture.path
        
        # Altera a imagem do usuário
        with open('path_to_new_image.jpg', 'rb') as img:
            new_image = SimpleUploadedFile('new_profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = new_image
            self.user.save()

        # Verifica se a imagem antiga foi deletada
        self.assertFalse(os.path.exists(old_image_path), f"A imagem antiga {old_image_path} não foi deletada quando a imagem foi alterada.")
        
        # Verifica se a nova imagem foi salva
        self.assertTrue(os.path.exists(self.user.profile_picture.path), "A nova imagem não foi salva.")

    def test_image_not_found_in_directory(self):
        """Testa se a imagem que foi removida da pasta é tratada como nova imagem"""
        # Adiciona uma imagem ao usuário
        with open('path_to_image.jpg', 'rb') as img:
            image = SimpleUploadedFile('profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = image
            self.user.save()

        # Salva o caminho da imagem antes de removê-la da pasta
        image_path = self.user.profile_picture.path

        # Remove a imagem do diretório (simulando que foi deletada fisicamente)
        os.remove(image_path)

        # Verifica se a imagem não está mais no diretório
        self.assertFalse(os.path.exists(image_path), f"A imagem {image_path} ainda existe no diretório.")

        # Atualiza a imagem do usuário com uma nova
        with open('path_to_new_image.jpg', 'rb') as img:
            new_image = SimpleUploadedFile('new_profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = new_image
            self.user.save()

        # Verifica se o sistema tratou a remoção da imagem e inseriu a nova corretamente
        self.assertTrue(os.path.exists(self.user.profile_picture.path), "A nova imagem não foi salva corretamente após a remoção da imagem anterior.")
