# myreport/accounts/tests/tests_views.py

from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AccountsAccessTests(TestCase):
    """
    Testa restrições e permissões de acesso para o app accounts.

    Regras:
    - login e register: apenas para não autenticados
    - demais rotas: apenas para autenticados

    Rodar:
    python manage.py test accounts.tests.tests_views.AccountsAccessTests
    """

    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPass!12345"

        cls.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.other = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password=cls.password,
            is_active=True,
        )

    def login(self):
        ok = self.client.login(username=self.user.username, password=self.password)
        self.assertTrue(ok)

    # ---------------------------
    # NÃO autenticado
    # ---------------------------

    def test_anonymous_can_access_login(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)

    def test_anonymous_can_access_register(self):
        resp = self.client.get(reverse("accounts:register"))
        self.assertEqual(resp.status_code, 200)

    def test_anonymous_cannot_access_profile_edit(self):
        resp = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_anonymous_cannot_access_password_change(self):
        resp = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_anonymous_cannot_access_user_list(self):
        resp = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_anonymous_cannot_access_user_profile(self):
        resp = self.client.get(
            reverse("accounts:user_profile", kwargs={"user_id": self.other.pk})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_anonymous_cannot_post_follow_toggle(self):
        resp = self.client.post(
            reverse("accounts:follow_toggle", kwargs={"user_id": self.other.pk}),
            data={"next": reverse("accounts:user_profile", kwargs={"user_id": self.other.pk})},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    # ---------------------------
    # Autenticado
    # ---------------------------

    def test_authenticated_cannot_access_register_redirects(self):
        self.login()
        resp = self.client.get(reverse("accounts:register"))
        self.assertEqual(resp.status_code, 302)
        # UserRegisterView.dispatch -> redirect("home:dashboard")
        self.assertIn(reverse("home:dashboard"), resp["Location"])

    def test_authenticated_cannot_access_login_redirects(self):
        self.login()
        # LoginView.redirect_authenticated_user = True
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 302)
        # normalmente vai para LOGIN_REDIRECT_URL / ou home:dashboard dependendo do projeto;
        # aqui o mínimo é garantir que NÃO fica na tela de login
        self.assertNotIn(reverse("accounts:login"), resp["Location"])

    def test_authenticated_can_access_profile_edit(self):
        self.login()
        resp = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_password_change(self):
        self.login()
        resp = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_user_list(self):
        self.login()
        resp = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_user_profile(self):
        self.login()
        resp = self.client.get(
            reverse("accounts:user_profile", kwargs={"user_id": self.other.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_post_follow_toggle_redirects(self):
        self.login()
        next_url = reverse("accounts:user_profile", kwargs={"user_id": self.other.pk})
        resp = self.client.post(
            reverse("accounts:follow_toggle", kwargs={"user_id": self.other.pk}),
            data={"next": next_url},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], next_url)

    def test_logout_works_with_get(self):
        self.login()
        resp = self.client.get(reverse("accounts:logout"))
        self.assertEqual(resp.status_code, 302)
        # user_logout -> redirect("home:index")
        self.assertIn(reverse("home:index"), resp["Location"])

    def test_logout_works_with_post(self):
        self.login()
        resp = self.client.post(reverse("accounts:logout"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("home:index"), resp["Location"])
