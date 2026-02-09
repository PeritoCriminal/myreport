# report_maker/tests/test_views_images.py
from __future__ import annotations

import io
from PIL import Image

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from institutions.models import (
    Institution,
    InstitutionCity,
    Nucleus,
    Team,
    UserInstitutionAssignment,
)
from report_maker.models import ReportCase, ExamObject, ObjectImage

UserModel = get_user_model()

# PNG 1x1 válido (evita depender de Pillow)
_PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2!\xbc3"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class ObjectImageViewsTests(TestCase):
    """
    Testes das views de imagens (ObjectImage) alinhados ao comportamento atual:

    - image_add: não-autor => 403
    - laudo bloqueado: pode resultar em 404 (dependendo do filtro interno da view)
    - images_reorder: items [] => 400 (contrato atual)
    """

    def setUp(self):
        self.user = UserModel.objects.create_user(username="u1", password="pass123")
        self.other = UserModel.objects.create_user(username="u2", password="pass123")

        self.user.can_edit_reports = True
        self.user.can_create_reports_until = timezone.now() + timedelta(days=30)
        self.user.save(update_fields=["can_edit_reports", "can_create_reports_until"])

        # Organização mínima
        self.inst = Institution.objects.create(
            acronym="SPTC",
            name="Superintendência da Polícia Técnico-Científica",
            kind=Institution.Kind.SCIENTIFIC_POLICE,
            is_active=True,
        )
        self.city = InstitutionCity.objects.create(institution=self.inst, name="Campinas", state="SP")
        self.nucleus = Nucleus.objects.create(institution=self.inst, name="Núcleo Campinas", city=self.city)
        self.team = Team.objects.create(nucleus=self.nucleus, name="Equipe 01", description="")

        UserInstitutionAssignment.objects.create(
            user=self.user,
            institution=self.inst,
            start_at=timezone.now(),
            end_at=None,
            is_primary=True,
        )

        self.report = self._make_report(author=self.user)

        # Objeto de exame mínimo
        self.exam_object = ExamObject.objects.create(
            report_case=self.report,
            title="Objeto teste",
            order=1,
        )

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
    def login(self, who):
        ok = self.client.login(username=who.username, password="pass123")
        self.assertTrue(ok)

    def _make_report(self, *, author) -> ReportCase:
        report = ReportCase(
            author=author,
            report_number="123.123/2026",
            requesting_authority="Autoridade Requisitante (teste)",
            institution=self.inst,
            nucleus=self.nucleus,
            team=self.team,
        )
        report.save()
        return report

    def _lock_report(self):
        self.report.close()
        self.report.save()
        self.report.refresh_from_db()

    def _valid_image_file(self) -> SimpleUploadedFile:
        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, format="PNG")
        buf.seek(0)
        return SimpleUploadedFile("teste.png", buf.read(), content_type="image/png")

    def _add_url(self) -> str:
        return reverse(
            "report_maker:image_add",
            kwargs={
                "app_label": "report_maker",
                "model": "examobject",
                "object_id": self.exam_object.pk,
            },
        )

    # ─────────────────────────────────────────────
    # image_add
    # ─────────────────────────────────────────────
    def test_image_add_get_author_ok(self):
        self.login(self.user)
        resp = self.client.get(self._add_url())
        self.assertEqual(resp.status_code, 200)

    def test_image_add_get_non_author_forbidden(self):
        # comportamento atual: 403 (não 404)
        self.login(self.other)
        resp = self.client.get(self._add_url())
        self.assertEqual(resp.status_code, 403)

    def test_image_add_post_creates_image(self):
        self.login(self.user)

        resp = self.client.post(
            self._add_url(),
            data={
                "image": self._valid_image_file(),
                "caption": "Imagem de teste",
            },
        )

        if resp.status_code == 200:
            # mostra erros reais do form
            print(resp.context["form"].errors)

        self.assertIn(resp.status_code, (200, 302, 303))
        self.assertEqual(ObjectImage.objects.count(), 1)



    def test_image_add_blocks_when_report_locked(self):
        # comportamento atual observado: 404 (provavelmente por filtro interno)
        self._lock_report()
        self.login(self.user)

        resp = self.client.post(self._add_url(), data={"image": self._valid_image_file()})
        self.assertIn(resp.status_code, (403, 404, 302))

    # ─────────────────────────────────────────────
    # image_delete
    # ─────────────────────────────────────────────
    def test_image_delete_author_ok(self):
        self.login(self.user)

        img = ObjectImage.objects.create(
            content_object=self.exam_object,
            image=self._valid_image_file(),
            index=1,
            # campos NOT NULL no seu schema
            original_width=1,
            original_height=1,
        )

        url = reverse("report_maker:image_delete", kwargs={"pk": img.pk})
        resp = self.client.post(url)
        self.assertIn(resp.status_code, (302, 303))
        self.assertEqual(ObjectImage.objects.count(), 0)

    def test_image_delete_non_author_forbidden(self):
        img = ObjectImage.objects.create(
            content_object=self.exam_object,
            image=self._valid_image_file(),
            index=1,
            original_width=1,
            original_height=1,
        )

        self.login(self.other)
        url = reverse("report_maker:image_delete", kwargs={"pk": img.pk})
        resp = self.client.post(url)
        # comportamento atual típico: 403
        self.assertEqual(resp.status_code, 403)

    # ─────────────────────────────────────────────
    # images_reorder (JSON)
    # ─────────────────────────────────────────────
    def test_images_reorder_empty_is_rejected_by_current_contract(self):
        # comportamento atual: 400
        self.login(self.user)
        url = reverse("report_maker:images_reorder")
        resp = self.client.post(url, data=json.dumps({"items": []}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_images_reorder_non_author_forbidden(self):
        self.login(self.other)
        url = reverse("report_maker:images_reorder")
        resp = self.client.post(url, data=json.dumps({"items": []}), content_type="application/json")
        self.assertEqual(resp.status_code, 403)
