from django.test import TestCase
from accountsapp.models.custom_user_model import CustomUserModel
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
import os, tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


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

    def create_temp_image(self, name="temp_image.jpg"):
        """Cria uma imagem temporária para os testes."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image = Image.new('RGB', (100, 100), color='red')
        image.save(temp_file, 'JPEG')
        temp_file.seek(0)
        return temp_file

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
        """Testa se a imagem é deletada ao excluir o usuário."""
        # Cria uma imagem temporária
        temp_image = self.create_temp_image()

        # Adiciona a imagem ao usuário
        with open(temp_image.name, 'rb') as img:
            image = SimpleUploadedFile('profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = image
            self.user.save()

        # Salva o caminho da imagem antes de deletar o usuário
        image_path = self.user.profile_picture.path

        # Deleta o usuário
        self.user.delete()

        # Verifica se a imagem foi deletada
        self.assertFalse(os.path.exists(image_path), f"A imagem {image_path} não foi deletada quando o usuário foi excluído.")

        # Remove o arquivo temporário
        temp_image.close()
        os.remove(temp_image.name)





    def test_image_updated_and_old_image_deleted(self):
        """Testa se a imagem antiga é deletada ao alterar a imagem do usuário."""
        # Cria imagens temporárias
        temp_image = self.create_temp_image()
        temp_new_image = self.create_temp_image(name="new_temp_image.jpg")

        # Adiciona uma imagem inicial ao usuário
        with open(temp_image.name, 'rb') as img:
            image = SimpleUploadedFile('profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = image
            self.user.save()

        # Salva o caminho da imagem antes de alterá-la
        old_image_path = self.user.profile_picture.path

        # Altera a imagem do usuário
        with open(temp_new_image.name, 'rb') as img:
            new_image = SimpleUploadedFile('new_profile_picture.jpg', img.read(), content_type='image/jpeg')
            self.user.profile_picture = new_image
            self.user.save()

        # Verifica se a imagem antiga foi deletada
        self.assertFalse(os.path.exists(old_image_path), f"A imagem antiga {old_image_path} não foi deletada quando a imagem foi alterada.")

        # Verifica se a nova imagem foi salva
        self.assertTrue(os.path.exists(self.user.profile_picture.path), "A nova imagem não foi salva.")

        # Remove os arquivos temporários
        temp_image.close()
        temp_new_image.close()
        os.remove(temp_image.name)
        os.remove(temp_new_image.name)



    def test_image_not_found_in_directory(self):
        """Testa se a imagem que foi removida da pasta é tratada como nova imagem."""
        # Cria arquivos temporários para as imagens
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img:
            temp_img.write(b'\x00\x01\x02')  # Simula o conteúdo de uma imagem
            temp_img_path = temp_img.name  # Caminho da imagem temporária

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_new_img:
            temp_new_img.write(b'\x03\x04\x05')  # Simula o conteúdo de uma nova imagem
            temp_new_img_path = temp_new_img.name  # Caminho da nova imagem temporária

        try:
            # Adiciona uma imagem ao usuário
            with open(temp_img_path, 'rb') as img:
                image = SimpleUploadedFile('profile_picture.jpg', img.read(), content_type='image/jpeg')
                self.user.profile_picture = image
                self.user.save()

            # Salva o caminho da imagem antes de removê-la da pasta
            image_path = self.user.profile_picture.path

            # Remove a imagem do diretório (simulando que foi deletada fisicamente)
            os.remove(image_path)

            # Verifica se a imagem foi removida
            self.assertFalse(os.path.exists(image_path), f"A imagem {image_path} ainda existe no diretório.")

            # Simula a lógica de tratamento no método save do modelo
            try:
                self.user.save()
            except Exception as e:
                self.assertIsInstance(e, FileNotFoundError, "O erro esperado ao salvar uma imagem inexistente não foi gerado.")

            # Atualiza a imagem do usuário com uma nova
            with open(temp_new_img_path, 'rb') as img:
                new_image = SimpleUploadedFile('new_profile_picture.jpg', img.read(), content_type='image/jpeg')
                self.user.profile_picture = new_image
                self.user.save()

            # Verifica se a nova imagem foi salva corretamente
            self.assertTrue(
                os.path.exists(self.user.profile_picture.path),
                "A nova imagem não foi salva corretamente após a remoção da imagem anterior."
            )

        finally:
            # Remove os arquivos temporários criados
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            if os.path.exists(temp_new_img_path):
                os.remove(temp_new_img_path)
