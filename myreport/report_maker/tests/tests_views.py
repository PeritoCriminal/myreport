# report_maker/tests/tests_views.py
from __future__ import annotations

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from institutions.models import (
    Institution,
    InstitutionCity,
    Nucleus,
    Team,
)
from report_maker.models import ReportCase
from report_maker.models.report_text_block import ReportTextBlock

UserModel = get_user_model()


class ReportMakerViewsSmokeTests(TestCase):
    """
    Smoke tests das views do app report_maker.

    Objetivo:
    - Garantir que as URLs principais respondem (200/302/403/404) conforme regras.
    - Verificar autor vs não-autor.
    - Verificar bloqueio de escrita quando o laudo não está editável.
    - Verificar bloqueio por expiração de can_create_reports (se aplicado na view).
    """

    def setUp(self):
        self.user = UserModel.objects.create_user(username="u1", password="pass123")
        self.other = UserModel.objects.create_user(username="u2", password="pass123")

        # Permissões do usuário (ajuste nomes se necessário)
        self.user.can_create_reports = True
        self.user.can_edit_reports = True
        self.user.can_create_reports_until = timezone.now() + timedelta(days=90)
        self.user.save(update_fields=["can_create_reports", "can_edit_reports", "can_create_reports_until"])

        # ─────────────────────────────────────────────
        # Organização mínima (exigida no close() / validação de laudo fechado)
        # ─────────────────────────────────────────────
        self.inst = Institution.objects.create(
            acronym="SPTC",
            name="Superintendência da Polícia Técnico-Científica",
            kind=Institution.Kind.SCIENTIFIC_POLICE,
            is_active=True,
        )
        self.city = InstitutionCity.objects.create(institution=self.inst, name="Campinas", state="SP")
        self.nucleus = Nucleus.objects.create(institution=self.inst, name="Núcleo Campinas", city=self.city)
        self.team = Team.objects.create(nucleus=self.nucleus, name="Equipe 01", description="")

        self.user.team = self.team

        self.user.save(
            update_fields=[
                "can_create_reports",
                "can_edit_reports",
                "can_create_reports_until",
                "team",
            ]
        )

        self.report = self._make_report(author=self.user, report_number="123.123/2026")

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
    def login(self, who):
        ok = self.client.login(username=who.username, password="pass123")
        self.assertTrue(ok)

    def _make_report(self, *, author, report_number: str = "000.000/0000") -> ReportCase:
        """
        Cria um ReportCase válido respeitando full_clean() no save().

        IMPORTANTE:
        - Seu model ReportCase chama full_clean() em save(), então precisamos
          preencher os campos obrigatórios.
        """
        base = dict(
            author=author,
            report_number=report_number,
            requesting_authority="Autoridade Requisitante (teste)",

            # Organização (permite close() nos testes e mantém consistência do domínio)
            institution=self.inst,
            nucleus=self.nucleus,
            team=self.team,
        )

        report = ReportCase(**base)

        try:
            report.save()
        except ValidationError as e:
            raise AssertionError(
                "ReportCase inválido no teste. Ajuste _make_report() com os mínimos obrigatórios.\n"
                f"Erros: {getattr(e, 'message_dict', e)}"
            )

        return report

    def _lock_report(self, report: ReportCase):
        """
        Torna report.can_edit == False usando o método de domínio.
        """
        report.close()
        report.save()
        report.refresh_from_db()
        return report

    # ─────────────────────────────────────────────
    # ReportCase: list/detail
    # ─────────────────────────────────────────────
    def test_reportcase_list_requires_login(self):
        url = reverse("report_maker:reportcase_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_reportcase_list_shows_only_own(self):
        self._make_report(author=self.other, report_number="999.999/2026")
        self.login(self.user)

        url = reverse("report_maker:reportcase_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "123.123/2026")
        self.assertNotContains(resp, "999.999/2026")

    def test_reportcase_detail_author_ok(self):
        self.login(self.user)
        url = reverse("report_maker:reportcase_detail", kwargs={"pk": self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_reportcase_detail_non_author_404(self):
        self.login(self.other)
        url = reverse("report_maker:reportcase_detail", kwargs={"pk": self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    # ─────────────────────────────────────────────
    # PDF
    # ─────────────────────────────────────────────
    def test_pdf_generator_only_author(self):
        self.login(self.other)
        url = reverse("report_maker:report_pdf", kwargs={"pk": self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        self.login(self.user)
        resp2 = self.client.get(url)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2["Content-Type"], "application/pdf")

    # ─────────────────────────────────────────────
    # Close (conclusão)
    # ─────────────────────────────────────────────
    def test_close_view_non_author_404(self):
        self.login(self.other)
        url = reverse("report_maker:reportcase_close", kwargs={"pk": self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_close_view_blocks_when_report_locked(self):
        self._lock_report(self.report)

        self.login(self.user)
        url = reverse("report_maker:reportcase_close", kwargs={"pk": self.report.pk})
        resp = self.client.get(url)

        # sua view faz redirect quando já está bloqueado
        self.assertIn(resp.status_code, (301, 302))

    # ─────────────────────────────────────────────
    # Reorder (exam_objects_reorder)
    # ─────────────────────────────────────────────
    def test_exam_objects_reorder_requires_owner(self):
        self.login(self.other)
        url = reverse("report_maker:exam_objects_reorder", kwargs={"pk": self.report.pk})
        resp = self.client.post(url, data=json.dumps({"items": []}), content_type="application/json")
        self.assertEqual(resp.status_code, 403)

    def test_exam_objects_reorder_blocks_when_report_locked(self):
        self.login(self.user)
        self._lock_report(self.report)

        url = reverse("report_maker:exam_objects_reorder", kwargs={"pk": self.report.pk})
        resp = self.client.post(
            url,
            data=json.dumps({"items": [{"id": "fake-id"}]}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    # ─────────────────────────────────────────────
    # Text blocks (create/upsert)
    # ─────────────────────────────────────────────
    def test_textblock_create_get_author_ok(self):
        self.login(self.user)
        url = reverse("report_maker:textblock_create", kwargs={"report_pk": self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_textblock_create_non_author_404(self):
        self.login(self.other)
        url = reverse("report_maker:textblock_create", kwargs={"report_pk": self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_textblock_upsert_redirects_to_create_when_missing(self):
        self.login(self.user)
        url = reverse(
            "report_maker:text_block_upsert",
            kwargs={"report_pk": self.report.pk, "placement": ReportTextBlock.Placement.SUMMARY},
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)

        expected = reverse("report_maker:textblock_create", kwargs={"report_pk": self.report.pk})
        self.assertTrue(resp.url.startswith(expected))
        self.assertIn("placement=SUMMARY", resp.url)


    def test_textblock_upsert_redirects_to_update_when_exists(self):
        self.login(self.user)
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        url = reverse(
            "report_maker:text_block_upsert",
            kwargs={"report_pk": self.report.pk, "placement": ReportTextBlock.Placement.SUMMARY},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(str(tb.pk), resp.url)

    # ─────────────────────────────────────────────
    # Permissão do usuário (expiração)
    # ─────────────────────────────────────────────
    def test_user_expired_cannot_open_reportcase_create_form(self):
        self.user.can_create_reports_until = timezone.now() - timedelta(days=1)
        self.user.save(update_fields=["can_create_reports_until"])

        self.login(self.user)
        url = reverse("report_maker:reportcase_create")
        resp = self.client.get(url)

        # depende do comportamento do seu mixin (403 ou redirect)
        self.assertIn(resp.status_code, (302, 403))

    def test_user_valid_can_open_reportcase_create_form(self):
        self.user.can_create_reports_until = timezone.now() + timedelta(days=10)
        self.user.save(update_fields=["can_create_reports_until"])

        self.login(self.user)
        url = reverse("report_maker:reportcase_create")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
