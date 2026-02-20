# report_maker/tests/test_views_reorder.py
from __future__ import annotations

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from institutions.models import Institution, InstitutionCity, Nucleus, Team
from report_maker.models import ReportCase

UserModel = get_user_model()


class ExamObjectsReorderContractTests(TestCase):
    """
    Testes de contrato (JSON) para a view report_maker:exam_objects_reorder.

    Foco:
    - payload inválido NÃO pode virar 500
    - deve responder com 400/415 conforme o contrato que você escolher
    - continua respeitando: autor vs não-autor e laudo bloqueado
    """

    def setUp(self):
        self.user = UserModel.objects.create_user(username="u1", password="pass123")
        self.other = UserModel.objects.create_user(username="u2", password="pass123")

        self.user.can_create_reports = True
        self.user.can_edit_reports = True
        self.user.can_create_reports_until = timezone.now().date() + timedelta(days=90)

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
                "can_edit_reports",
                "can_create_reports",
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

    def url(self) -> str:
        return reverse("report_maker:exam_objects_reorder", kwargs={"pk": self.report.pk})

    def post_json(self, payload: dict, *, content_type="application/json"):
        return self.client.post(self.url(), data=json.dumps(payload), content_type=content_type)

    # ─────────────────────────────────────────────
    # Contrato: erros de payload (evitar 500)
    # ─────────────────────────────────────────────
    def test_reorder_rejects_non_json_content_type(self):
        """
        Sugestão de contrato: se não for JSON, retornar 415 (ou 400).
        Ajuste o assert conforme sua decisão.
        """
        self.login(self.user)
        resp = self.client.post(self.url(), data="{}", content_type="text/plain")
        self.assertIn(resp.status_code, (400, 415))

    def test_reorder_rejects_malformed_json(self):
        """
        JSON inválido deve retornar 400 (não pode virar 500).
        """
        self.login(self.user)
        resp = self.client.post(self.url(), data="{", content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_reorder_requires_items_key(self):
        """
        Sugestão: payload sem 'items' => 400.
        """
        self.login(self.user)
        resp = self.post_json({"x": 1})
        self.assertEqual(resp.status_code, 400)

    def test_reorder_items_must_be_list(self):
        self.login(self.user)
        resp = self.post_json({"items": "nao-e-lista"})
        self.assertEqual(resp.status_code, 400)

    def test_reorder_item_requires_id(self):
        """
        Sugestão: cada item precisa ter id.
        """
        self.login(self.user)
        resp = self.post_json({"items": [{"pos": 1}]})
        self.assertEqual(resp.status_code, 400)

    # ─────────────────────────────────────────────
    # Contrato: sucesso mínimo
    # ─────────────────────────────────────────────
    def test_reorder_accepts_empty_items(self):
        """
        Mesmo sem objetos, 'items': [] deve ser aceito (200),
        pois o front pode mandar 'lista vazia' em cenários de limpeza.
        """
        self.login(self.user)
        resp = self.post_json({"items": []})
        self.assertEqual(resp.status_code, 200)

    # ─────────────────────────────────────────────
    # Permissões / bloqueios (reforço)
    # ─────────────────────────────────────────────
    def test_reorder_non_author_forbidden(self):
        self.login(self.other)
        resp = self.post_json({"items": []})
        self.assertEqual(resp.status_code, 403)

    def test_reorder_blocks_when_report_locked(self):
        self.login(self.user)
        self._lock_report(self.report)
        resp = self.post_json({"items": []})
        self.assertEqual(resp.status_code, 403)
