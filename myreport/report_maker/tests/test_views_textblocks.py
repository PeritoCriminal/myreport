# report_maker/tests/test_views_textblocks.py
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
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
from report_maker.models import ReportCase
from report_maker.models.report_text_block import ReportTextBlock

UserModel = get_user_model()


class ReportTextBlockViewsTests(TestCase):
    """
    Testes das views de ReportTextBlock, alinhados ao comportamento esperado do sistema:

    - Autor vs não-autor
    - Bloqueio quando o laudo está fechado (can_edit=False)
    - Create/Update/Delete
    - Upsert por placement (redireciona para create ou update)
    """

    def setUp(self):
        self.user = UserModel.objects.create_user(username="u1", password="pass123")
        self.other = UserModel.objects.create_user(username="u2", password="pass123")

        # Permissões do usuário (mixin costuma depender disso)
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

    def _list_url(self) -> str:
        return reverse("report_maker:textblock_list", kwargs={"report_pk": self.report.pk})

    def _create_url(self) -> str:
        return reverse("report_maker:textblock_create", kwargs={"report_pk": self.report.pk})

    def _update_url(self, tb: ReportTextBlock) -> str:
        return reverse("report_maker:textblock_update", kwargs={"report_pk": self.report.pk, "pk": tb.pk})

    def _delete_url(self, tb: ReportTextBlock) -> str:
        return reverse("report_maker:textblock_delete", kwargs={"report_pk": self.report.pk, "pk": tb.pk})

    def _upsert_url(self, placement: str) -> str:
        return reverse(
            "report_maker:text_block_upsert",
            kwargs={"report_pk": self.report.pk, "placement": placement},
        )

    # ─────────────────────────────────────────────
    # Create
    # ─────────────────────────────────────────────
    def test_textblock_create_get_author_ok(self):
        self.login(self.user)
        resp = self.client.get(self._create_url())
        self.assertEqual(resp.status_code, 200)

    def test_textblock_create_get_non_author_404(self):
        self.login(self.other)
        resp = self.client.get(self._create_url())
        self.assertEqual(resp.status_code, 404)

    def test_textblock_create_post_creates_and_redirects(self):
        self.login(self.user)

        resp = self.client.post(
            self._create_url(),
            data={
                "placement": ReportTextBlock.Placement.SUMMARY,
                "body": "Texto de teste",
                "position": 1,
            },
        )

        self.assertIn(resp.status_code, (302, 303))
        self.assertEqual(ReportTextBlock.objects.filter(report_case=self.report).count(), 1)

    def test_textblock_create_blocks_when_report_locked(self):
        self._lock_report()
        self.login(self.user)

        resp = self.client.post(
            self._create_url(),
            data={
                "placement": ReportTextBlock.Placement.SUMMARY,
                "body": "Texto de teste",
                "position": 1,
            },
        )

        # dependendo do filtro/mixin, pode virar 403 ou 404 ou redirect
        self.assertIn(resp.status_code, (302, 403, 404))
        self.assertEqual(ReportTextBlock.objects.filter(report_case=self.report).count(), 0)

    # ─────────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────────
    def test_textblock_update_get_author_ok(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        self.login(self.user)
        resp = self.client.get(self._update_url(tb))
        self.assertEqual(resp.status_code, 200)

    def test_textblock_update_non_author_404(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        self.login(self.other)
        resp = self.client.get(self._update_url(tb))
        self.assertEqual(resp.status_code, 404)

    def test_textblock_update_post_updates_and_redirects(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        self.login(self.user)
        resp = self.client.post(
            self._update_url(tb),
            data={
                "placement": tb.placement,
                "body": "novo texto",
                "position": tb.position,
            },
        )

        self.assertIn(resp.status_code, (302, 303))
        tb.refresh_from_db()
        self.assertEqual(tb.body, "novo texto")

    def test_textblock_update_blocks_when_report_locked(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )
        self._lock_report()

        self.login(self.user)
        resp = self.client.post(
            self._update_url(tb),
            data={
                "placement": tb.placement,
                "body": "tentativa de alterar",
                "position": tb.position,
            },
        )

        self.assertIn(resp.status_code, (302, 403, 404))
        tb.refresh_from_db()
        self.assertEqual(tb.body, "abc")

    # ─────────────────────────────────────────────
    # Delete
    # ─────────────────────────────────────────────
    def test_textblock_delete_author_ok(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        self.login(self.user)
        resp = self.client.post(self._delete_url(tb))
        self.assertIn(resp.status_code, (302, 303))
        self.assertFalse(ReportTextBlock.objects.filter(pk=tb.pk).exists())

    def test_textblock_delete_non_author_404(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        self.login(self.other)
        resp = self.client.post(self._delete_url(tb))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(ReportTextBlock.objects.filter(pk=tb.pk).exists())

    def test_textblock_delete_blocks_when_report_locked(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )
        self._lock_report()

        self.login(self.user)
        resp = self.client.post(self._delete_url(tb))
        self.assertIn(resp.status_code, (302, 403, 404))
        self.assertTrue(ReportTextBlock.objects.filter(pk=tb.pk).exists())

    # ─────────────────────────────────────────────
    # Upsert
    # ─────────────────────────────────────────────
    def test_textblock_upsert_redirects_to_create_when_missing(self):
        self.login(self.user)
        resp = self.client.get(self._upsert_url(ReportTextBlock.Placement.SUMMARY))

        self.assertEqual(resp.status_code, 302)
        expected = self._create_url()
        self.assertTrue(resp.url.startswith(expected))
        self.assertIn("placement=SUMMARY", resp.url)

    def test_textblock_upsert_redirects_to_update_when_exists(self):
        tb = ReportTextBlock.objects.create(
            report_case=self.report,
            placement=ReportTextBlock.Placement.SUMMARY,
            body="abc",
            position=1,
        )

        self.login(self.user)
        resp = self.client.get(self._upsert_url(ReportTextBlock.Placement.SUMMARY))

        self.assertEqual(resp.status_code, 302)
        self.assertIn(str(tb.pk), resp.url)

    def test_textblock_upsert_non_author_404(self):
        self.login(self.other)
        resp = self.client.get(self._upsert_url(ReportTextBlock.Placement.SUMMARY))
        self.assertEqual(resp.status_code, 404)
