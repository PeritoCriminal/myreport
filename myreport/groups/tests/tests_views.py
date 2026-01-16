# myreport/groups/tests/tests_views.py

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from groups.models import Group, GroupMembership


class GroupsViewsTests(TestCase):
    """
    Testa restrições, permissões e fluxos principais das views do app groups.

    Regras gerais:
    - todas as rotas exigem usuário autenticado (LoginRequiredMixin / @login_required)
    - apenas o criador pode editar ou desativar o grupo
    - feed do grupo só é acessível por membros ou criador
    - join/leave/deactivate apenas via POST (require_POST)
    - grupo inativo: detail só para criador; feed redireciona para detail (não-criador)
    """

    @classmethod
    def setUpTestData(cls):
        cls.password = "TestPass!12345"

        cls.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.group = Group.objects.create(
            name="Grupo de Teste",
            description="Descrição",
            creator=cls.creator,
            is_active=True,
        )

        # creator e member são membros
        GroupMembership.objects.create(group=cls.group, user=cls.creator)
        GroupMembership.objects.create(group=cls.group, user=cls.member)

    def login(self, user):
        ok = self.client.login(username=user.username, password=self.password)
        self.assertTrue(ok)

    def assert_login_redirect(self, resp, path):
        """
        LoginRequiredMixin/@login_required costumam redirecionar para:
        /accounts/login/?next=<path> (ou equivalente)
        """
        login_url = reverse("accounts:login")
        expected = f"{login_url}?next={path}"
        self.assertRedirects(resp, expected, fetch_redirect_response=False)

    # -------------------------------------------------
    # ANÔNIMO: tudo redireciona para login
    # -------------------------------------------------

    def test_anonymous_cannot_access_group_list(self):
        url = reverse("groups:group_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_group_detail(self):
        url = reverse("groups:group_detail", kwargs={"pk": self.group.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_group_create(self):
        url = reverse("groups:group_create")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_group_feed(self):
        url = reverse("groups:group_feed", kwargs={"pk": self.group.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_join_group(self):
        url = reverse("groups:group_join", kwargs={"pk": self.group.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_leave_group(self):
        url = reverse("groups:group_leave", kwargs={"pk": self.group.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_deactivate_group(self):
        url = reverse("groups:group_deactivate", kwargs={"pk": self.group.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    # -------------------------------------------------
    # AUTENTICADO: acessos gerais
    # -------------------------------------------------

    def test_authenticated_can_access_group_list(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_list"))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_group_detail(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_detail", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_group_create(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_create"))
        self.assertEqual(resp.status_code, 200)

    # -------------------------------------------------
    # CREATE: criador vira membro automaticamente
    # -------------------------------------------------

    def test_creator_is_member_after_group_creation(self):
        self.login(self.other)

        resp = self.client.post(
            reverse("groups:group_create"),
            {"name": "Novo Grupo", "description": "Teste"},
        )
        self.assertEqual(resp.status_code, 302)

        group = Group.objects.get(name="Novo Grupo")

        self.assertTrue(
            GroupMembership.objects.filter(group=group, user=self.other).exists()
        )

    # -------------------------------------------------
    # UPDATE: permissões
    # -------------------------------------------------

    def test_only_creator_can_edit_group(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_update", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_creator_can_edit_group(self):
        self.login(self.creator)
        resp = self.client.get(reverse("groups:group_update", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 200)

    # -------------------------------------------------
    # DEACTIVATE: POST-only + permissões
    # -------------------------------------------------

    def test_deactivate_rejects_get(self):
        self.login(self.creator)
        resp = self.client.get(reverse("groups:group_deactivate", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_only_creator_can_deactivate_group(self):
        self.login(self.other)
        resp = self.client.post(reverse("groups:group_deactivate", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_creator_can_deactivate_group(self):
        self.login(self.creator)
        resp = self.client.post(reverse("groups:group_deactivate", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

        self.group.refresh_from_db()
        self.assertFalse(self.group.is_active)

        # Garantia: não remove membership do criador
        self.assertTrue(
            GroupMembership.objects.filter(group=self.group, user=self.creator).exists()
        )

    # -------------------------------------------------
    # DETAIL: grupo inativo só para criador
    # -------------------------------------------------

    def test_non_creator_cannot_access_inactive_group_detail(self):
        self.group.is_active = False
        self.group.save(update_fields=["is_active"])

        self.login(self.member)
        resp = self.client.get(reverse("groups:group_detail", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_creator_can_access_inactive_group_detail(self):
        self.group.is_active = False
        self.group.save(update_fields=["is_active"])

        self.login(self.creator)
        resp = self.client.get(reverse("groups:group_detail", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 200)

    # -------------------------------------------------
    # FEED: membro/criador ok; não-membro e inativo → redirect para detail
    # -------------------------------------------------

    def test_member_can_access_group_feed(self):
        self.login(self.member)
        resp = self.client.get(reverse("groups:group_feed", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_creator_can_access_group_feed(self):
        self.login(self.creator)
        resp = self.client.get(reverse("groups:group_feed", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_non_member_is_redirected_from_group_feed(self):
        self.login(self.other)
        url = reverse("groups:group_feed", kwargs={"pk": self.group.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(
            resp,
            reverse("groups:group_detail", kwargs={"pk": self.group.pk}),
            fetch_redirect_response=False,
        )


    def test_member_cannot_access_feed_of_inactive_group(self):
        self.group.is_active = False
        self.group.save(update_fields=["is_active"])

        self.login(self.member)
        resp = self.client.get(reverse("groups:group_feed", kwargs={"pk": self.group.pk}))

        self.assertRedirects(
            resp,
            reverse("groups:group_detail", kwargs={"pk": self.group.pk}),
            fetch_redirect_response=False,
        )

    # -------------------------------------------------
    # JOIN / LEAVE: POST-only + efeitos no banco
    # -------------------------------------------------

    def test_join_rejects_get(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_join", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_leave_rejects_get(self):
        self.login(self.member)
        resp = self.client.get(reverse("groups:group_leave", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_authenticated_can_join_group(self):
        self.login(self.other)
        resp = self.client.post(reverse("groups:group_join", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(
            GroupMembership.objects.filter(group=self.group, user=self.other).exists()
        )

    def test_user_cannot_join_group_twice(self):
        self.login(self.member)

        self.client.post(reverse("groups:group_join", kwargs={"pk": self.group.pk}))
        self.client.post(reverse("groups:group_join", kwargs={"pk": self.group.pk}))

        self.assertEqual(
            GroupMembership.objects.filter(group=self.group, user=self.member).count(),
            1
        )

    def test_authenticated_can_leave_group(self):
        self.login(self.member)
        resp = self.client.post(reverse("groups:group_leave", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

        self.assertFalse(
            GroupMembership.objects.filter(group=self.group, user=self.member).exists()
        )

    def test_non_member_can_call_leave_safely(self):
        self.login(self.other)
        resp = self.client.post(reverse("groups:group_leave", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_cannot_join_inactive_group(self):
        self.group.is_active = False
        self.group.save(update_fields=["is_active"])

        self.login(self.other)
        resp = self.client.post(reverse("groups:group_join", kwargs={"pk": self.group.pk}))

        self.assertEqual(resp.status_code, 403)
