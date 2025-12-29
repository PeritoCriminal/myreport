# myreport/groups/tests/tests_views.py

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from groups.models import Group, GroupMembership


class GroupsAccessTests(TestCase):
    """
    Testa restrições e permissões de acesso para o app groups.

    Regras gerais:
    - todas as rotas exigem usuário autenticado
    - apenas o criador pode editar ou desativar o grupo
    - feed do grupo só é acessível por membros ou criador
    - join/leave apenas via POST
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

        GroupMembership.objects.create(
            group=cls.group,
            user=cls.creator,
        )

        GroupMembership.objects.create(
            group=cls.group,
            user=cls.member,
        )

    def login(self, user):
        ok = self.client.login(username=user.username, password=self.password)
        self.assertTrue(ok)

    # -------------------------------------------------
    # ANÔNIMO: tudo redireciona para login
    # -------------------------------------------------

    def test_anonymous_cannot_access_group_list(self):
        resp = self.client.get(reverse("groups:group_list"))
        self.assertEqual(resp.status_code, 302)

    def test_anonymous_cannot_access_group_detail(self):
        resp = self.client.get(reverse("groups:group_detail", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

    def test_anonymous_cannot_access_group_create(self):
        resp = self.client.get(reverse("groups:group_create"))
        self.assertEqual(resp.status_code, 302)

    def test_anonymous_cannot_access_group_feed(self):
        resp = self.client.get(reverse("groups:group_feed", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

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

    def test_authenticated_can_create_group(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_create"))
        self.assertEqual(resp.status_code, 200)

    # -------------------------------------------------
    # PERMISSÕES ESPECÍFICAS
    # -------------------------------------------------

    def test_only_creator_can_edit_group(self):
        self.login(self.other)
        resp = self.client.get(reverse("groups:group_update", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_creator_can_edit_group(self):
        self.login(self.creator)
        resp = self.client.get(reverse("groups:group_update", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_only_creator_can_deactivate_group(self):
        self.login(self.other)
        resp = self.client.post(reverse("groups:group_deactivate", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_creator_can_deactivate_group(self):
        self.login(self.creator)
        resp = self.client.post(reverse("groups:group_deactivate", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)

        self.group.refresh_from_db()
        self.assertFalse(self.group.is_active)

    # -------------------------------------------------
    # FEED DO GRUPO
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
        resp = self.client.get(reverse("groups:group_feed", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("groups:group_detail", kwargs={"pk": self.group.pk}), resp["Location"])

    # -------------------------------------------------
    # JOIN / LEAVE
    # -------------------------------------------------

    def test_authenticated_can_join_group(self):
        self.login(self.other)
        resp = self.client.post(reverse("groups:group_join", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            GroupMembership.objects.filter(group=self.group, user=self.other).exists()
        )

    def test_authenticated_can_leave_group(self):
        self.login(self.member)
        resp = self.client.post(reverse("groups:group_leave", kwargs={"pk": self.group.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            GroupMembership.objects.filter(group=self.group, user=self.member).exists()
        )
