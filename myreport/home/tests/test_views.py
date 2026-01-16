# home/tests/test_views.py

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from social_net.models import Post, PostHidden


User = get_user_model()


class HomeAccessTests(TestCase):
    """
    Testa restrições e permissões de acesso para o app home.
    comando para rodar a class: python manage.py test home.tests.test_views.HomeAccessTests
    """

    @classmethod
    def setUpTestData(cls):
        cls.password = "SenhaForte123!"

        cls.user = User.objects.create_user(
            username="teste",
            email="teste@exemplo.com",
            password=cls.password,
        )

        cls.other_user = User.objects.create_user(
            username="outro",
            email="outro@exemplo.com",
            password=cls.password,
        )

    # ----------------------------
    # INDEX
    # ----------------------------

    def test_index_allows_anonymous(self):
        url = reverse("home:index")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/index.html")

    def test_index_redirects_authenticated_to_dashboard(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse("home:index")
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse("home:dashboard"))

    # ----------------------------
    # DASHBOARD (acesso)
    # ----------------------------

    def test_dashboard_requires_login(self):
        url = reverse("home:dashboard")
        resp = self.client.get(url)
        login_url = reverse("accounts:login")
        self.assertRedirects(resp, f"{login_url}?next={url}")

    def test_dashboard_allows_authenticated_user(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse("home:dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/dashboard.html")

    # ----------------------------
    # DASHBOARD (contexto)
    # ----------------------------

    def test_dashboard_excluded_posts_limit_and_order(self):
        self.client.login(username=self.user.username, password=self.password)

        # cria 6 posts inativos do próprio usuário
        for i in range(6):
            p = Post.objects.create(
                user=self.user,
                title=f"Inativo {i}",
                is_active=False,
            )
            # força updated_at crescente
            Post.objects.filter(pk=p.pk).update(
                updated_at=timezone.now() + timedelta(minutes=i)
            )

        resp = self.client.get(reverse("home:dashboard"))
        self.assertEqual(resp.status_code, 200)

        excluded = list(resp.context["excluded_posts"])

        # limita a 5
        self.assertEqual(len(excluded), 5)

        # ordenação: mais recente primeiro
        self.assertEqual(excluded[0].title, "Inativo 5")
        self.assertEqual(excluded[-1].title, "Inativo 1")

    def test_dashboard_hidden_posts_only_active_and_limited(self):
        self.client.login(username=self.user.username, password=self.password)

        # cria 6 posts ativos (de outro usuário)
        active_posts = []
        for i in range(6):
            p = Post.objects.create(
                user=self.other_user,
                title=f"Ativo {i}",
                is_active=True,
            )
            Post.objects.filter(pk=p.pk).update(
                updated_at=timezone.now() + timedelta(minutes=i)
            )
            active_posts.append(p)

        # cria 1 post inativo (não deve aparecer em hidden_posts)
        inactive = Post.objects.create(
            user=self.other_user,
            title="Inativo",
            is_active=False,
        )

        # oculta todos para o usuário logado
        for p in active_posts:
            PostHidden.objects.create(post=p, user=self.user)
        PostHidden.objects.create(post=inactive, user=self.user)

        resp = self.client.get(reverse("home:dashboard"))
        self.assertEqual(resp.status_code, 200)

        hidden = resp.context["hidden_posts"]

        # só ativos
        self.assertTrue(all(p.is_active for p in hidden))

        # limite 5
        self.assertEqual(len(hidden), 5)

        # ordenação correta (mais recente primeiro)
        self.assertEqual(hidden[0].title, "Ativo 5")

    # ----------------------------
    # ZEN DO LAUDO
    # ----------------------------

    def test_zen_do_laudo_requires_login(self):
        url = reverse("home:zen_do_laudo")
        resp = self.client.get(url)
        login_url = reverse("accounts:login")
        self.assertRedirects(resp, f"{login_url}?next={url}")

    def test_zen_do_laudo_allows_authenticated_user(self):
        self.client.login(username=self.user.username, password=self.password)
        url = reverse("home:zen_do_laudo")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home/zen_do_laudo.html")
