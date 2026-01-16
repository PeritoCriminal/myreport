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
    UserInstitutionAssignment,
)
from report_maker.models import ReportCase


def make_pdf_file(name="laudo.pdf", content=b"%PDF-1.4\n%Fake PDF\n"):
    return SimpleUploadedFile(name=name, content=content, content_type="application/pdf")


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
        UserInstitutionAssignment.objects.create(
            user=cls.user,
            institution=cls.inst,
            start_at=timezone.now(),
            end_at=None,
            is_primary=True,
        )

        # Núcleo / Equipe (para unit_line / snapshots)
        cls.city = InstitutionCity.objects.create(institution=cls.inst, name="Campinas", state="SP")
        cls.nucleus = Nucleus.objects.create(institution=cls.inst, name="Núcleo Campinas", city=cls.city)
        cls.team = Team.objects.create(nucleus=cls.nucleus, name="Equipe 01", description="")

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
        report.close(pdf_file=make_pdf_file("final.pdf"))
        report.save()
        report.refresh_from_db()
        return report

    def test_close_freezes_organization_snapshot_and_header_stays_stable_after_institution_changes(self):
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
        self.assertEqual(report.institution_name_snapshot, "Superintendência da Polícia Técnico-Científica")
        self.assertEqual(report.nucleus_name_snapshot, "Núcleo Campinas")
        self.assertEqual(report.team_name_snapshot, "Equipe 01")
        self.assertEqual(report.honoree_title_snapshot, "Perito Criminal Dr.")
        self.assertEqual(report.honoree_name_snapshot, "Octávio Eduardo de Brito Alvarenga")
        self.assertEqual(report.institution_kind_snapshot, str(self.inst.kind))

        header_before = report.header_context
        snap_primary_name_before = report.emblem_primary_snapshot.name if report.emblem_primary_snapshot else ""
        snap_secondary_name_before = report.emblem_secondary_snapshot.name if report.emblem_secondary_snapshot else ""

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
        self.assertEqual(report.institution_name_for_display, "Superintendência da Polícia Técnico-Científica")
        self.assertEqual(report.nucleus_display, "Núcleo Campinas")
        self.assertEqual(report.team_display, "Equipe 01")

        # Header deve permanecer estável
        header_after = report.header_context
        self.assertEqual(header_after["acronym"], header_before["acronym"])
        self.assertEqual(header_after["name"], header_before["name"])
        self.assertEqual(header_after["honoree_line"], header_before["honoree_line"])
        self.assertEqual(header_after["unit_line"], header_before["unit_line"])

        # Emblemas devem continuar apontando para snapshot gravado no laudo
        snap_primary_name_after = report.emblem_primary_snapshot.name if report.emblem_primary_snapshot else ""
        snap_secondary_name_after = report.emblem_secondary_snapshot.name if report.emblem_secondary_snapshot else ""
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

        # Encerra o vínculo do usuário (simula troca de base/instituição/demissão)
        assign = self.user.active_institution_assignment
        self.assertIsNotNone(assign)
        assign.end_at = timezone.now()
        assign.save(update_fields=["end_at"])

        self.user.refresh_from_db()
        self.assertFalse(self.user.can_edit_reports_effective)

        report.refresh_from_db()
        self.assertTrue(report.is_frozen)

        # Continua renderizando por snapshot
        hdr = report.header_context
        self.assertEqual(hdr["acronym"], report.institution_acronym_snapshot or None)
        self.assertEqual(hdr["name"], report.institution_name_snapshot or None)
        self.assertEqual(hdr["unit_line"], "Núcleo Campinas - Equipe 01")
