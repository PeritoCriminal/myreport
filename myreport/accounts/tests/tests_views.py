# accounts/tests/tests_views.py

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
            data={
                "next": reverse(
                    "accounts:user_profile", kwargs={"user_id": self.other.pk}
                )
            },
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
        # mínimo: garantir que NÃO fica na tela de login
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


class AccountsSecurityHardeningTests(TestCase):
    """
    Testes específicos de endurecimento contra acesso não autorizado/abuso:
    - AJAX protegido por login
    - open-redirect bloqueado no follow_toggle
    - follow_toggle: follow self e alvo inativo
    - user_list não expõe usuários inativos
    """

    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPass!12345"

        cls.user = User.objects.create_user(
            username="sec_user1",
            email="sec_user1@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.other = User.objects.create_user(
            username="sec_user2",
            email="sec_user2@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.inactive = User.objects.create_user(
            username="sec_inactive",
            email="sec_inactive@example.com",
            password=cls.password,
            is_active=False,
        )

    def login(self):
        ok = self.client.login(username=self.user.username, password=self.password)
        self.assertTrue(ok)

    def test_anonymous_can_access_ajax_nuclei(self):
        url = reverse("accounts:ajax_nuclei")

        resp = self.client.get(url, {"institution": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(resp.json(), {"results": []})

    def test_anonymous_can_access_ajax_teams(self):
        url = reverse("accounts:ajax_teams")

        resp = self.client.get(url, {"nucleus": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(resp.json(), {"results": []})

    def test_follow_toggle_rejects_external_next_url(self):
        self.login()

        resp = self.client.post(
            reverse("accounts:follow_toggle", kwargs={"user_id": self.other.pk}),
            data={"next": "https://evil.com"},
        )

        self.assertEqual(resp.status_code, 302)
        # Deve redirecionar para dentro do sistema (fallback)
        self.assertIn(
            reverse("accounts:user_profile", kwargs={"user_id": self.other.pk}),
            resp["Location"],
        )

    def test_authenticated_cannot_follow_self_returns_400(self):
        self.login()

        resp = self.client.post(
            reverse("accounts:follow_toggle", kwargs={"user_id": self.user.pk})
        )
        self.assertEqual(resp.status_code, 400)

    def test_follow_toggle_target_inactive_returns_404(self):
        self.login()

        resp = self.client.post(
            reverse("accounts:follow_toggle", kwargs={"user_id": self.inactive.pk})
        )
        self.assertEqual(resp.status_code, 404)

    def test_user_list_excludes_inactive_users(self):
        self.login()

        resp = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, self.inactive.username)


class AccountsDefaultHomeRedirectTests(TestCase):
    """
    Testa o redirect pós-login conforme default_home do usuário.
    """

    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPass!12345"

        cls.user = User.objects.create_user(
            username="pref_user",
            email="pref_user@example.com",
            password=cls.password,
            is_active=True,
        )

    def test_login_redirects_to_selected_home(self):
        self.user.default_home = "technical"
        self.user.save(update_fields=["default_home"])

        resp = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
            follow=False,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            reverse("technical_repository:document_list"),
        )

    def test_login_falls_back_to_dashboard_when_home_invalid(self):
        self.user.default_home = "pagina_inexistente"
        self.user.save(update_fields=["default_home"])

        resp = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
            follow=False,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            reverse("home:dashboard"),
        )
