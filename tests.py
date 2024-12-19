from django.test import TestCase
from accountsapp.models.custom_user_model import CustomUserModel
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError


class CustomUserModelTest(TestCase):

    def setUp(self):
        # Cria um usuário base para os testes
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
