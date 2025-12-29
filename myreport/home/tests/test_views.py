# home/tests/test_views.py

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class HomeAccessTests(TestCase):
    """
    Testa de restrições e permissões de acesso para o app home.
    comando para rodar a class: python manage.py test home.tests.test_views.HomeAccessTests
    """
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="teste",
            email="teste@exemplo.com",
            password="SenhaForte123!",
        )


    def test_index_allows_anonymous(self):
        url = reverse("home:index")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/index.html")


    def test_index_redirects_authenticated_to_dashboard(self):
        self.client.login(username="teste", password="SenhaForte123!")
        url = reverse("home:index")
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("home:dashboard"))


    def test_dashboard_requires_login(self):
        url = reverse("home:dashboard")
        resp = self.client.get(url)
        login_url = reverse("accounts:login")
        self.assertRedirects(resp, f"{login_url}?next={url}")


    def test_dashboard_allows_authenticated_user(self):
        self.client.login(username="teste", password="SenhaForte123!")
        url = reverse("home:dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/dashboard.html")


    def test_zen_do_laudo_requires_login(self):
        url = reverse("home:zen_do_laudo")
        resp = self.client.get(url)
        login_url = reverse("accounts:login")
        self.assertRedirects(resp, f"{login_url}?next={url}")


    def test_zen_do_laudo_allows_authenticated_user(self):
        self.client.login(username="teste", password="SenhaForte123!")
        url = reverse("home:zen_do_laudo")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/zen_do_laudo.html")
