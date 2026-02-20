# report_maker/tests/tests_models.py

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from PIL import Image

from institutions.models import (
    Institution,
    InstitutionCity,
    Nucleus,
    Team,
)
from report_maker.models import ReportCase


def make_png_file(name="img.png", size=(20, 20)):
    bio = BytesIO()
    Image.new("RGB", size).save(bio, format="PNG")
    bio.seek(0)
    return SimpleUploadedFile(name=name, content=bio.read(), content_type="image/png")


class ReportCaseSnapshotModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="u1", password="pass12345")
        cls.user.can_edit_reports = True
        cls.user.save(update_fields=["can_edit_reports"])

        # Instituição + vínculo ativo (não é requisito do model, mas reflete o domínio)
        cls.inst = Institution.objects.create(
            acronym="SPTC",
            name="Superintendência da Polícia Técnico-Científica",
            kind=Institution.Kind.SCIENTIFIC_POLICE,
            honoree_title="Perito Criminal Dr.",
            honoree_name="Octávio Eduardo de Brito Alvarenga",
            emblem_primary=make_png_file("emblem_a.png"),
            emblem_secondary=make_png_file("emblem_b.png"),
            is_active=True,
        )

        # Núcleo / Equipe (para unit_line / snapshots)
        cls.city = InstitutionCity.objects.create(
            institution=cls.inst, name="Campinas", state="SP"
        )
        cls.nucleus = Nucleus.objects.create(
            institution=cls.inst, name="Núcleo Campinas", city=cls.city
        )
        cls.team = Team.objects.create(
            nucleus=cls.nucleus, name="Equipe 01", description=""
        )

        # Novo modelo: vínculo institucional é inferido por user.team
        cls.user.team = cls.team
        cls.user.save(update_fields=["team"])

    def _create_open_report(self):
        return ReportCase.objects.create(
            report_number="99/2026",
            protocol="",
            author=self.user,
            institution=self.inst,
            nucleus=self.nucleus,
            team=self.team,
            objective=ReportCase.Objective.INITIAL_EXAM,
            requesting_authority="Autoridade",
            status=ReportCase.Status.OPEN,
            is_locked=False,
        )

    def _close_report(self, report: ReportCase):
        report.close()
        report.save()
        report.refresh_from_db()
        return report

    def test_close_freezes_organization_snapshot_and_header_stays_stable_after_institution_changes(
        self,
    ):
        """
        Garante:
        - close() preenche snapshots e marca organization_frozen_at
        - após congelado, mudanças na Institution NÃO alteram header_context/display do laudo
        """
        report = self._create_open_report()

        # Antes de fechar, OPEN usa FK (nome atual)
        self.assertFalse(report.is_frozen)
        self.assertEqual(report.institution_name_for_display, self.inst.name)

        report = self._close_report(report)

        # Depois de fechar, snapshots preenchidos
        self.assertTrue(report.is_frozen)
        self.assertIsNotNone(report.organization_frozen_at)

        self.assertEqual(report.institution_acronym_snapshot, "SPTC")
        self.assertEqual(
            report.institution_name_snapshot, "Superintendência da Polícia Técnico-Científica"
        )
        self.assertEqual(report.nucleus_name_snapshot, "Núcleo Campinas")
        self.assertEqual(report.team_name_snapshot, "Equipe 01")
        self.assertEqual(report.honoree_title_snapshot, "Perito Criminal Dr.")
        self.assertEqual(report.honoree_name_snapshot, "Octávio Eduardo de Brito Alvarenga")
        self.assertEqual(report.institution_kind_snapshot, self.inst.get_kind_display())

        # Snapshot REAL (cópia): não pode apontar para o mesmo caminho do arquivo da Institution
        self.assertTrue(report.emblem_primary_snapshot)
        self.assertTrue(report.emblem_secondary_snapshot)
        self.assertNotEqual(report.emblem_primary_snapshot.name, self.inst.emblem_primary.name)
        self.assertNotEqual(
            report.emblem_secondary_snapshot.name, self.inst.emblem_secondary.name
        )

        # Caminho esperado do snapshot
        self.assertIn(f"reports/{report.id}/header/", report.emblem_primary_snapshot.name)
        self.assertIn(f"reports/{report.id}/header/", report.emblem_secondary_snapshot.name)

        header_before = report.header_context
        snap_primary_name_before = (
            report.emblem_primary_snapshot.name if report.emblem_primary_snapshot else ""
        )
        snap_secondary_name_before = (
            report.emblem_secondary_snapshot.name if report.emblem_secondary_snapshot else ""
        )

        # Muda a Institution "no mundo real" (nome/acrônimo/honraria/emblemas)
        self.inst.acronym = "XPTC"
        self.inst.name = "Instituição Renomeada"
        self.inst.honoree_title = "Dr."
        self.inst.honoree_name = "Fulano"
        self.inst.emblem_primary = make_png_file("emblem_new_primary.png")
        self.inst.emblem_secondary = make_png_file("emblem_new_secondary.png")
        self.inst.save()

        report.refresh_from_db()

        # Display do laudo deve permanecer pelo snapshot
        self.assertEqual(report.institution_acronym_for_display, "SPTC")
        self.assertEqual(
            report.institution_name_for_display, "Superintendência da Polícia Técnico-Científica"
        )
        self.assertEqual(report.nucleus_display, "Núcleo Campinas")
        self.assertEqual(report.team_display, "Equipe 01")

        # Header deve permanecer estável
        header_after = report.header_context
        self.assertEqual(header_after["acronym"], header_before["acronym"])
        self.assertEqual(header_after["name"], header_before["name"])
        self.assertEqual(header_after["honoree_line"], header_before["honoree_line"])
        self.assertEqual(header_after["unit_line"], header_before["unit_line"])

        # Emblemas devem continuar apontando para snapshot gravado no laudo
        snap_primary_name_after = (
            report.emblem_primary_snapshot.name if report.emblem_primary_snapshot else ""
        )
        snap_secondary_name_after = (
            report.emblem_secondary_snapshot.name if report.emblem_secondary_snapshot else ""
        )
        self.assertEqual(snap_primary_name_after, snap_primary_name_before)
        self.assertEqual(snap_secondary_name_after, snap_secondary_name_before)

    def test_frozen_report_blocks_changes_in_fk_and_snapshots(self):
        """
        Garante:
        - após congelado, não é possível alterar institution/nucleus/team
        - após congelado, não é possível alterar campos snapshot
        """
        report = self._close_report(self._create_open_report())

        inst2 = Institution.objects.create(
            acronym="PC",
            name="Polícia Civil",
            kind=Institution.Kind.CIVIL_POLICE,
            is_active=True,
        )

        # Tentar trocar FK após congelado -> ValidationError
        report.institution = inst2
        with self.assertRaises(ValidationError):
            report.save()

        report.refresh_from_db()

        # Tentar mexer em snapshot após congelado -> ValidationError
        report.institution_name_snapshot = "HACK"
        with self.assertRaises(ValidationError):
            report.save()

    def test_report_stays_frozen_even_if_user_loses_institution_assignment(self):
        """
        Garante que o laudo fechado não depende do vínculo institucional ativo do usuário.
        (o usuário pode perder a lotação e o laudo permanece renderizável via snapshot)
        """
        report = self._close_report(self._create_open_report())

        # Remove a equipe do usuário (simula troca de base/instituição/demissão)
        self.user.team = None
        self.user.save(update_fields=["team"])

        self.user.refresh_from_db()
        self.assertFalse(self.user.can_edit_reports_effective)

        report.refresh_from_db()
        self.assertTrue(report.is_frozen)

        # Continua renderizando por snapshot
        hdr = report.header_context
        self.assertEqual(hdr["acronym"], report.institution_acronym_snapshot or None)
        self.assertEqual(hdr["name"], report.institution_name_snapshot or None)
        self.assertEqual(hdr["unit_line"], "Núcleo Campinas - Equipe 01")

    def _read_file_bytes(self, field) -> bytes:
        if not field:
            return b""
        field.open("rb")
        try:
            return field.read()
        finally:
            field.close()

    def test_close_requires_organization_fields(self):
        """
        Garante que não é possível concluir laudo sem institution/nucleus/team,
        pois o fechamento congela snapshots institucionais.
        """
        report = ReportCase.objects.create(
            report_number="100/2026",
            protocol="",
            author=self.user,
            institution=None,
            nucleus=None,
            team=None,
            objective=ReportCase.Objective.INITIAL_EXAM,
            requesting_authority="Autoridade",
            status=ReportCase.Status.OPEN,
            is_locked=False,
        )

        report.close()
        with self.assertRaises(ValidationError):
            report.save()

    def test_close_is_idempotent_for_snapshots(self):
        """
        Garante que chamar close() novamente não regrava snapshots nem altera organization_frozen_at.
        (congelamento ocorre uma única vez)
        """
        report = self._close_report(self._create_open_report())

        frozen_at_1 = report.organization_frozen_at
        snap_primary_1 = (
            report.emblem_primary_snapshot.name if report.emblem_primary_snapshot else ""
        )
        snap_secondary_1 = (
            report.emblem_secondary_snapshot.name if report.emblem_secondary_snapshot else ""
        )
        inst_name_snap = report.institution_name_snapshot
        acr_snap = report.institution_acronym_snapshot
        hon_snap = report.honoree_name_snapshot
        kind_snap = report.institution_kind_snapshot

        # Chamada repetida
        report.close()
        report.save()
        report.refresh_from_db()

        self.assertEqual(report.organization_frozen_at, frozen_at_1)
        self.assertEqual(
            report.emblem_primary_snapshot.name if report.emblem_primary_snapshot else "",
            snap_primary_1,
        )
        self.assertEqual(
            report.emblem_secondary_snapshot.name if report.emblem_secondary_snapshot else "",
            snap_secondary_1,
        )
        self.assertEqual(report.institution_name_snapshot, inst_name_snap)
        self.assertEqual(report.institution_acronym_snapshot, acr_snap)
        self.assertEqual(report.honoree_name_snapshot, hon_snap)
        self.assertEqual(report.institution_kind_snapshot, kind_snap)

    def test_emblem_snapshot_content_equals_source_at_close_time(self):
        """
        Garante que o snapshot do emblema é uma cópia real do conteúdo no momento do fechamento.
        """
        report = self._close_report(self._create_open_report())

        src_primary_bytes = self._read_file_bytes(self.inst.emblem_primary)
        src_secondary_bytes = self._read_file_bytes(self.inst.emblem_secondary)
        snap_primary_bytes = self._read_file_bytes(report.emblem_primary_snapshot)
        snap_secondary_bytes = self._read_file_bytes(report.emblem_secondary_snapshot)

        self.assertEqual(snap_primary_bytes, src_primary_bytes)
        self.assertEqual(snap_secondary_bytes, src_secondary_bytes)

    def test_header_context_uses_snapshots_when_frozen(self):
        """
        Garante que, após congelado, o header_context é derivado exclusivamente dos snapshots,
        mesmo que a Institution mude seus dados.
        """
        report = self._close_report(self._create_open_report())

        hdr_before = report.header_context

        # muda a instituição
        self.inst.acronym = "ALT"
        self.inst.name = "Instituição Alterada"
        self.inst.honoree_title = "Dr."
        self.inst.honoree_name = "Beltrano"
        self.inst.save()

        report.refresh_from_db()
        hdr_after = report.header_context

        self.assertEqual(hdr_after["acronym"], hdr_before["acronym"])
        self.assertEqual(hdr_after["name"], hdr_before["name"])
        self.assertEqual(hdr_after["honoree_line"], hdr_before["honoree_line"])
        self.assertEqual(hdr_after["unit_line"], hdr_before["unit_line"])