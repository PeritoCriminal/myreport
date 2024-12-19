from django.test import TestCase
from django.urls import reverse
from accountsapp.models import CustomUserModel  # Certifique-se de importar o modelo correto

class UserViewTest(TestCase):
    def setUp(self):
        # Criação de um usuário de teste com o modelo CustomUserModel
        self.user = CustomUserModel.objects.create_user(username='testuser', password='12345')
        self.url = reverse('user')  # Use o nome correto da URL 'user' definido em urls.py

    def test_redirects_unauthenticated_user(self):
        # Testa que um usuário não autenticado é redirecionado para a página de login
        response = self.client.get(self.url)
        self.assertRedirects(response, '/accounts/login/?next=' + self.url)  # Atualize o caminho para /accounts/login

    def test_authenticated_user_accesses_user_page(self):
        # Testa que um usuário autenticado pode acessar a página user.html
        self.client.login(username='testuser', password='12345')  # Loga o usuário de teste
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)  # Verifica se a resposta foi bem-sucedida
        self.assertTemplateUsed(response, 'user.html')  # Verifica se o template correto foi usado
