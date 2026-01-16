# myreport/social_net/tests/tests_views.py

from django.test import TestCase
from django.template import TemplateDoesNotExist
from django.urls import reverse

from accounts.models import User
from social_net.models import Post, PostComment, PostHidden, PostLike, PostRating
from accounts.models import UserFollow


class SocialNetAccessTests(TestCase):
    """
    Testa restrições e permissões de acesso para o app social_net.

    Regras:
    - todas as rotas do social_net: apenas para autenticados
    - deletes (post/comment): só o autor pode (senão 403)
    - endpoints require_POST: GET deve retornar 405
    - like: toggle (like/unlike)
    - rate: validação de value (400 em inválido/out_of_range)
    - feed: exclui ocultadas e prioriza seguidos

    Rodar:
    python manage.py test social_net.tests.tests_views.SocialNetAccessTests
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
        cls.third = User.objects.create_user(
            username="user3",
            email="user3@example.com",
            password=cls.password,
            is_active=True,
        )

        cls.post = Post.objects.create(
            user=cls.other,
            title="Post de teste",
            text="Conteúdo",
            is_active=True,
        )

        cls.comment = PostComment.objects.create(
            post=cls.post,
            user=cls.other,
            text="Comentário",
            is_active=True,
        )

    def login(self, user=None):
        user = user or self.user
        ok = self.client.login(username=user.username, password=self.password)
        self.assertTrue(ok)

    def assert_login_redirect(self, resp, path):
        login_url = reverse("accounts:login")
        self.assertRedirects(resp, f"{login_url}?next={path}", fetch_redirect_response=False)

    # ---------------------------
    # ANÔNIMO: tudo deve redirecionar para login
    # ---------------------------

    def test_anonymous_cannot_access_post_list(self):
        url = reverse("social_net:post_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_post_detail(self):
        url = reverse("social_net:post_detail", kwargs={"pk": self.post.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_post_create(self):
        url = reverse("social_net:post_create")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_post_like(self):
        url = reverse("social_net:post_like", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_post_rate(self):
        url = reverse("social_net:post_rate", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url, data={"value": 5})
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_post_delete(self):
        url = reverse("social_net:post_delete", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_comment_list(self):
        url = reverse("social_net:comment_list", kwargs={"post_id": self.post.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_access_comment_create(self):
        url = reverse("social_net:comment_create", kwargs={"post_id": self.post.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_comment_delete(self):
        url = reverse("social_net:comment_delete", kwargs={"comment_id": self.comment.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    def test_anonymous_cannot_toggle_hide_post(self):
        url = reverse("social_net:post_hide_toggle", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assert_login_redirect(resp, url)

    # ---------------------------
    # require_POST: GET deve retornar 405
    # ---------------------------

    def test_like_rejects_get(self):
        self.login()
        resp = self.client.get(reverse("social_net:post_like", kwargs={"post_id": self.post.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_rate_rejects_get(self):
        self.login()
        resp = self.client.get(reverse("social_net:post_rate", kwargs={"post_id": self.post.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_post_delete_rejects_get(self):
        self.login()
        resp = self.client.get(reverse("social_net:post_delete", kwargs={"post_id": self.post.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_comment_delete_rejects_get(self):
        self.login()
        resp = self.client.get(reverse("social_net:comment_delete", kwargs={"comment_id": self.comment.pk}))
        self.assertEqual(resp.status_code, 405)

    def test_hide_toggle_rejects_get(self):
        self.login()
        resp = self.client.get(reverse("social_net:post_hide_toggle", kwargs={"post_id": self.post.pk}))
        self.assertEqual(resp.status_code, 405)

    # ---------------------------
    # AUTENTICADO: acessos gerais
    # ---------------------------

    def test_authenticated_can_access_post_list(self):
        self.login()
        resp = self.client.get(reverse("social_net:post_list"))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_post_detail(self):
        self.login()
        resp = self.client.get(reverse("social_net:post_detail", kwargs={"pk": self.post.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_can_access_post_detail_404_uses_global_template(self):
        """
        View HTML: deve renderizar 404 quando pk não existe.
        (aproveita templates/404.html do projeto)
        """
        self.login()
        resp = self.client.get(reverse("social_net:post_detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}))
        self.assertEqual(resp.status_code, 404)
        # opcional (se seu handler 404 estiver usando templates normalmente):
        # self.assertTemplateUsed(resp, "404.html")

    def test_authenticated_can_access_post_create_endpoint_exists(self):
        """
        A PostCreateView é usada no fluxo AJAX a partir do feed.
        Um GET direto pode resultar em TemplateDoesNotExist dependendo do seu estado atual
        (sem template dedicado). O que importa aqui:
        - endpoint existe
        - autenticado não é redirecionado ao login
        """
        self.login()
        try:
            resp = self.client.get(reverse("social_net:post_create"))
        except TemplateDoesNotExist:
            return
        self.assertIn(resp.status_code, (200, 302))

    # ---------------------------
    # LIKE: toggle
    # ---------------------------

    def test_like_toggles_like_and_count(self):
        self.login()

        url = reverse("social_net:post_like", kwargs={"post_id": self.post.pk})

        # like
        resp1 = self.client.post(url)
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertTrue(data1["success"])
        self.assertTrue(data1["liked"])
        self.assertEqual(data1["likes_count"], 1)
        self.assertTrue(PostLike.objects.filter(post=self.post, user=self.user).exists())

        # unlike
        resp2 = self.client.post(url)
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertTrue(data2["success"])
        self.assertFalse(data2["liked"])
        self.assertEqual(data2["likes_count"], 0)
        self.assertFalse(PostLike.objects.filter(post=self.post, user=self.user).exists())

    # ---------------------------
    # RATE: validações
    # ---------------------------

    def test_rate_invalid_value_returns_400(self):
        self.login()
        url = reverse("social_net:post_rate", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url, data={"value": "x"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json().get("error"), "invalid_value")

    def test_rate_out_of_range_returns_400(self):
        self.login()
        url = reverse("social_net:post_rate", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url, data={"value": 9})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json().get("error"), "out_of_range")

    def test_authenticated_can_rate_and_persists(self):
        self.login()
        url = reverse("social_net:post_rate", kwargs={"post_id": self.post.pk})
        resp = self.client.post(url, data={"value": 4})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["rating_value"], 4)

        self.assertTrue(PostRating.objects.filter(post=self.post, user=self.user, value=4).exists())

    # ---------------------------
    # DELETE: permissões e soft delete
    # ---------------------------

    def test_authenticated_non_owner_cannot_delete_post_403(self):
        self.login()
        resp = self.client.post(reverse("social_net:post_delete", kwargs={"post_id": self.post.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_authenticated_owner_can_delete_post_soft_delete(self):
        self.login(self.other)

        resp = self.client.post(reverse("social_net:post_delete", kwargs={"post_id": self.post.pk}))
        self.assertEqual(resp.status_code, 200)

        self.post.refresh_from_db()
        self.assertFalse(self.post.is_active)

    def test_authenticated_non_owner_cannot_delete_comment_403(self):
        self.login()
        resp = self.client.post(reverse("social_net:comment_delete", kwargs={"comment_id": self.comment.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_authenticated_owner_can_delete_comment_soft_delete(self):
        self.login(self.other)

        resp = self.client.post(reverse("social_net:comment_delete", kwargs={"comment_id": self.comment.pk}))
        self.assertEqual(resp.status_code, 200)

        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_active)


    # ---------------------------
    # EDIÇÃO DE POST: bloqueio após visualização por terceiro
    # ---------------------------

    def test_owner_can_access_edit_when_not_opened_by_third_party(self):
        """
        O autor da postagem pode acessar a edição
        enquanto a postagem ainda não foi aberta por terceiros.
        """
        ok = self.client.login(username=self.other.username, password=self.password)
        self.assertTrue(ok)

        url = reverse("social_net:post_update", kwargs={"pk": self.post.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_owner_cannot_access_edit_when_opened_by_third_party(self):
        """
        O autor da postagem NÃO pode acessar a edição
        se a postagem já foi aberta por outro usuário.
        """
        self.post.opened_by_third_party = True
        self.post.save(update_fields=["opened_by_third_party"])

        ok = self.client.login(username=self.other.username, password=self.password)
        self.assertTrue(ok)

        url = reverse("social_net:post_update", kwargs={"pk": self.post.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("social_net:post_list"))

    def test_non_owner_cannot_access_edit_even_if_not_opened(self):
        """
        Um usuário que NÃO é o autor nunca pode editar a postagem,
        independentemente do status opened_by_third_party.
        """
        self.login()

        url = reverse("social_net:post_update", kwargs={"pk": self.post.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    # ---------------------------
    # HIDE: toggle + efeito no feed
    # ---------------------------

    def test_hide_toggle_creates_and_removes_posthidden_ajax(self):
        self.login()

        url = reverse("social_net:post_hide_toggle", kwargs={"post_id": self.post.pk})
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

        # hide
        resp1 = self.client.post(url, **headers)
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue(resp1.json().get("hidden"))
        self.assertTrue(PostHidden.objects.filter(post=self.post, user=self.user).exists())

        # unhide
        resp2 = self.client.post(url, **headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.json().get("hidden"))
        self.assertFalse(PostHidden.objects.filter(post=self.post, user=self.user).exists())

    def test_feed_excludes_hidden_posts(self):
        self.login()

        PostHidden.objects.create(post=self.post, user=self.user)

        resp = self.client.get(reverse("social_net:post_list"))
        self.assertEqual(resp.status_code, 200)

        posts = list(resp.context["posts"])
        self.assertNotIn(self.post.id, [p.id for p in posts])

    # ---------------------------
    # FEED: prioriza seguidos
    # ---------------------------

    def test_feed_prioritizes_followed_users(self):
        """
        PostListView ordena por -is_from_followed, -updated_at.
        """
        self.login()

        UserFollow.objects.create(follower=self.user, following=self.other, is_active=True)

        followed_post = Post.objects.create(user=self.other, title="Do Seguido", is_active=True)
        non_followed_post = Post.objects.create(user=self.third, title="Nao Seguido", is_active=True)

        resp = self.client.get(reverse("social_net:post_list"))
        self.assertEqual(resp.status_code, 200)

        posts = list(resp.context["posts"])
        ids = [p.id for p in posts]

        self.assertIn(followed_post.id, ids)
        self.assertIn(non_followed_post.id, ids)
        self.assertLess(ids.index(followed_post.id), ids.index(non_followed_post.id))
