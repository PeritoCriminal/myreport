# technical_repository/tests/tests_views.py

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from technical_repository.models import TechnicalTopic, TechnicalDocument


def make_pdf_file(name="doc.pdf", content=b"%PDF-1.4\n%Fake PDF\n"):
    return SimpleUploadedFile(
        name=name,
        content=content,
        content_type="application/pdf",
    )


class TechnicalRepositoryViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(username="u1", password="pass12345")
        cls.user2 = User.objects.create_user(username="u2", password="pass12345")

        cls.topic = TechnicalTopic.objects.create(
            name="Balística",
            slug="balistica",
            is_active=True,
        )

        cls.doc_active_u1 = TechnicalDocument.objects.create(
            title="Doc A",
            description="",
            topic=cls.topic,
            pdf_file=make_pdf_file("a.pdf"),
            created_by=cls.user1,
            is_active=True,
        )

        cls.doc_inactive_u1 = TechnicalDocument.objects.create(
            title="Doc Inativo",
            description="",
            topic=cls.topic,
            pdf_file=make_pdf_file("inativo.pdf"),
            created_by=cls.user1,
            is_active=False,
        )

    # ─────────────────────────────────────────────
    # LIST
    # ─────────────────────────────────────────────
    def test_list_requires_login(self):
        url = reverse("technical_repository:document_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_list_shows_only_active(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.doc_active_u1.title)
        self.assertNotContains(resp, self.doc_inactive_u1.title)

    # ─────────────────────────────────────────────
    # DETAIL
    # ─────────────────────────────────────────────
    def test_detail_requires_login(self):
        url = reverse("technical_repository:document_detail", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_detail_active_ok(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_detail", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.doc_active_u1.title)

    def test_detail_inactive_404_uses_template(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_detail", kwargs={"pk": self.doc_inactive_u1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, "404.html")

    # ─────────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────────
    def test_create_requires_login(self):
        url = reverse("technical_repository:document_create")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_create_success_sets_created_by(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_create")

        payload = {
            "title": "Novo Doc",
            "description": "Desc",
            "topic": self.topic.pk,
            "pdf_file": make_pdf_file("novo.pdf"),
        }
        resp = self.client.post(url, data=payload, follow=False)
        self.assertEqual(resp.status_code, 302)

        created = TechnicalDocument.objects.get(title="Novo Doc")
        self.assertEqual(created.created_by, self.user1)
        self.assertTrue(created.is_active)

    def test_create_rejects_non_pdf_extension(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_create")

        payload = {
            "title": "Doc Ruim",
            "description": "",
            "topic": self.topic.pk,
            "pdf_file": make_pdf_file("arquivo.txt"),  # extensão errada
        }
        resp = self.client.post(url, data=payload)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)

        form = resp.context["form"]
        self.assertIn("pdf_file", form.errors)
        self.assertIn("O arquivo deve estar no formato PDF.", form.errors["pdf_file"])

        self.assertFalse(TechnicalDocument.objects.filter(title="Doc Ruim").exists())

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────
    def test_update_requires_login(self):
        """
        No seu projeto, update (UserPassesTestMixin com raise_exception=True)
        está retornando 403 para usuário anônimo (em vez de redirect 302).
        """
        url = reverse("technical_repository:document_update", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, "403.html")

    def test_update_forbidden_uses_403_template(self):
        self.client.login(username="u2", password="pass12345")
        url = reverse("technical_repository:document_update", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, "403.html")

    def test_update_creator_can_edit(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_update", kwargs={"pk": self.doc_active_u1.pk})

        payload = {
            "title": "Doc A (editado)",
            "description": "x",
            "topic": self.topic.pk,
            "pdf_file": make_pdf_file("a2.pdf"),
        }
        resp = self.client.post(url, data=payload, follow=False)
        self.assertEqual(resp.status_code, 302)

        self.doc_active_u1.refresh_from_db()
        self.assertEqual(self.doc_active_u1.title, "Doc A (editado)")

    def test_update_inactive_404_uses_template(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_update", kwargs={"pk": self.doc_inactive_u1.pk})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, "404.html")

    # ─────────────────────────────────────────────
    # DELETE (lógico via POST)
    # ─────────────────────────────────────────────
    def test_delete_requires_login(self):
        """
        No seu projeto, delete (UserPassesTestMixin com raise_exception=True)
        está retornando 403 para usuário anônimo (em vez de redirect 302).
        """
        url = reverse("technical_repository:document_delete", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, "403.html")

    def test_delete_forbidden_uses_403_template(self):
        self.client.login(username="u2", password="pass12345")
        url = reverse("technical_repository:document_delete", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, "403.html")

        self.doc_active_u1.refresh_from_db()
        self.assertTrue(self.doc_active_u1.is_active)

    def test_delete_creator_sets_inactive_and_redirects(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_delete", kwargs={"pk": self.doc_active_u1.pk})
        resp = self.client.post(url, follow=False)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("technical_repository:document_list"))

        self.doc_active_u1.refresh_from_db()
        self.assertFalse(self.doc_active_u1.is_active)

    def test_delete_inactive_404_uses_template(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("technical_repository:document_delete", kwargs={"pk": self.doc_inactive_u1.pk})
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 404) 
        self.assertTemplateUsed(resp, "404.html")
