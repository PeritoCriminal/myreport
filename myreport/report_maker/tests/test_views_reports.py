# report_maker/tests/test_views_reports.py
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

UserModel = get_user_model()


class ReportCaseViewsTests(TestCase):
    """
    Testes principais das views de laudo (ReportCase).

    Cobertura (núcleo):
    - list/detail: autor vs não-autor (onde aplicável)
    - create/update: fluxo feliz
    - bloqueio (report.close -> can_edit False) barrando update
    - smoke de PDF (se existir rota)
    """

    def setUp(self):
        self.user = UserModel.objects.create_user(username="u1", password="pass123")
        self.other = UserModel.objects.create_user(username="u2", password="pass123")

        # Permissões do usuário (mixin costuma depender disso)
        self.user.can_edit_reports = True
        self.user.can_create_reports = True
        self.user.can_create_reports_until = timezone.now() + timedelta(days=30)
        self.user.save(update_fields=["can_edit_reports", "can_create_reports", "can_create_reports_until"])

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

        self.report = self._make_report(author=self.user, report_number="123.123/2026")

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
    def login(self, who):
        ok = self.client.login(username=who.username, password="pass123")
        self.assertTrue(ok)

    def _make_report(self, *, author, report_number: str) -> ReportCase:
        report = ReportCase(
            author=author,
            report_number=report_number,
            requesting_authority="Autoridade Requisitante (teste)",
            institution=self.inst,
            nucleus=self.nucleus,
            team=self.team,
        )
        report.save()
        return report

    def _lock_report(self, report: ReportCase):
        report.close()
        report.save()
        report.refresh_from_db()
        return report

    # URLs (ajuste se seus names forem diferentes)
    def _list_url(self) -> str:
        return reverse("report_maker:reportcase_list")

    def _create_url(self) -> str:
        return reverse("report_maker:reportcase_create")

    def _detail_url(self, report: ReportCase) -> str:
        return reverse("report_maker:reportcase_detail", kwargs={"pk": report.pk})

    def _update_url(self, report: ReportCase) -> str:
        return reverse("report_maker:reportcase_update", kwargs={"pk": report.pk})

    def _pdf_url(self, report: ReportCase) -> str:
        # Se seu name for outro, ajuste aqui.
        return reverse("report_maker:report_pdf", kwargs={"pk": report.pk})

    # ─────────────────────────────────────────────
    # List / Detail
    # ─────────────────────────────────────────────
    def test_report_list_requires_login(self):
        resp = self.client.get(self._list_url())
        self.assertIn(resp.status_code, (302, 301))

    def test_report_list_author_ok(self):
        self.login(self.user)
        resp = self.client.get(self._list_url())
        self.assertEqual(resp.status_code, 200)

    def test_report_detail_author_ok(self):
        self.login(self.user)
        resp = self.client.get(self._detail_url(self.report))
        self.assertEqual(resp.status_code, 200)

    def test_report_detail_non_author_404(self):
        self.login(self.other)
        resp = self.client.get(self._detail_url(self.report))
        self.assertEqual(resp.status_code, 404)

    # ─────────────────────────────────────────────
    # Create
    # ─────────────────────────────────────────────
    def test_report_create_get_author_ok(self):
        self.login(self.user)
        resp = self.client.get(self._create_url())
        self.assertEqual(resp.status_code, 200)

    def test_report_create_post_creates_and_redirects(self):
        self.login(self.user)

        resp = self.client.post(
            self._create_url(),
            data={
                "report_number": "111.222/2026",
                "requesting_authority": "Autoridade Requisitante (teste)",
                "institution": self.inst.pk,
                "nucleus": self.nucleus.pk,
                "team": self.team.pk,
                "criminal_typification": "Acidente de trânsito",
            },
        )
        self.assertIn(resp.status_code, (302, 303))
        self.assertTrue(ReportCase.objects.filter(report_number="111.222/2026", author=self.user).exists())

    def test_report_create_requires_permission(self):
        self.user.can_create_reports = False
        self.user.save(update_fields=["can_create_reports"])

        self.login(self.user)
        resp = self.client.get(self._create_url())
        self.assertIn(resp.status_code, (403, 302))

    # ─────────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────────
    def test_report_update_get_author_ok(self):
        self.login(self.user)
        resp = self.client.get(self._update_url(self.report))
        self.assertEqual(resp.status_code, 200)

    def test_report_update_post_updates_and_redirects(self):
        self.login(self.user)

        resp = self.client.post(
            self._update_url(self.report),
            data={
                "report_number": self.report.report_number,
                "requesting_authority": "Autoridade alterada",
                "institution": self.inst.pk,
                "nucleus": self.nucleus.pk,
                "team": self.team.pk,
                "criminal_typification": "Acidente de trânsito",
            },
        )
        self.assertIn(resp.status_code, (302, 303))
        self.report.refresh_from_db()
        self.assertEqual(self.report.requesting_authority, "Autoridade alterada")

    def test_report_update_non_author_forbidden(self):
        self.login(self.other)
        resp = self.client.get(self._update_url(self.report))
        self.assertEqual(resp.status_code, 403)

    def test_report_update_blocks_when_report_locked(self):
        self._lock_report(self.report)
        self.login(self.user)

        resp = self.client.post(
            self._update_url(self.report),
            data={
                "report_number": self.report.report_number,
                "requesting_authority": "Tentativa",
                "institution": self.inst.pk,
                "nucleus": self.nucleus.pk,
                "team": self.team.pk,
                "criminal_typification": "Acidente de trânsito",
            },
        )
        self.assertIn(resp.status_code, (403, 404, 302))
        self.report.refresh_from_db()
        self.assertNotEqual(self.report.requesting_authority, "Tentativa")

    # ─────────────────────────────────────────────
    # PDF (smoke)
    # ─────────────────────────────────────────────
    def test_report_pdf_author_ok_if_route_exists(self):
        """
        Smoke test: se a rota existir, deve responder 200/302.

        Se não existir no seu projeto, comente este teste ou ajuste o name da URL.
        """
        self.login(self.user)

        try:
            url = self._pdf_url(self.report)
        except Exception:
            self.skipTest("Rota de PDF não configurada (report_maker:report_pdf).")

        resp = self.client.get(url)
        self.assertIn(resp.status_code, (200, 302, 303))

    def test_report_pdf_non_author_404_if_route_exists(self):
        self.login(self.other)

        try:
            url = self._pdf_url(self.report)
        except Exception:
            self.skipTest("Rota de PDF não configurada (report_maker:report_pdf).")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
