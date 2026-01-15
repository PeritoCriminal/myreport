# institutions/tests/test_models.py

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from institutions.models import (
    Institution,
    InstitutionCity,
    Nucleus,
    Team,
    UserInstitutionAssignment,
    UserTeamAssignment,
)


class InstitutionModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.inst = Institution.objects.create(
            acronym="SPTC",
            name="Superintendência da Polícia Técnico-Científica",
            kind=Institution.Kind.SCIENTIFIC_POLICE,
        )

    def test_str_contains_acronym_and_name(self):
        s = str(self.inst)
        self.assertIn("SPTC", s)
        self.assertIn("Superintendência", s)

    def test_header_honoree_none_when_no_honoree_name(self):
        self.inst.honoree_title = "Perito Criminal Dr."
        self.inst.honoree_name = ""
        self.inst.save(update_fields=["honoree_title", "honoree_name"])

        header = self.inst.header
        self.assertIsNone(header.get("honoree"))

    def test_header_honoree_uses_title_and_name_when_both_present(self):
        self.inst.honoree_title = "Perito Criminal Dr."
        self.inst.honoree_name = "Octávio Eduardo de Brito Alvarenga"
        self.inst.save(update_fields=["honoree_title", "honoree_name"])

        header = self.inst.header
        self.assertEqual(
            header.get("honoree"),
            "Perito Criminal Dr. Octávio Eduardo de Brito Alvarenga",
        )

    def test_header_honoree_uses_name_when_title_blank(self):
        self.inst.honoree_title = ""
        self.inst.honoree_name = "Octávio Eduardo de Brito Alvarenga"
        self.inst.save(update_fields=["honoree_title", "honoree_name"])

        header = self.inst.header
        self.assertEqual(header.get("honoree"), "Octávio Eduardo de Brito Alvarenga")


class InstitutionCityModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.inst = Institution.objects.create(
            acronym="PCSP",
            name="Polícia Civil",
            kind=Institution.Kind.CIVIL_POLICE,
        )

    def test_unique_city_per_institution(self):
        InstitutionCity.objects.create(institution=self.inst, name="Limeira", state="SP")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InstitutionCity.objects.create(
                    institution=self.inst, name="Limeira", state="SP"
                )

    def test_same_city_name_allowed_for_different_state(self):
        InstitutionCity.objects.create(institution=self.inst, name="Limeira", state="SP")
        # outro estado = permitido
        InstitutionCity.objects.create(institution=self.inst, name="Limeira", state="MG")


class NucleusModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.inst = Institution.objects.create(
            acronym="IML",
            name="Instituto Médico-Legal",
            kind=Institution.Kind.MEDICAL_LEGAL,
        )

    def test_unique_nucleus_name_per_institution(self):
        Nucleus.objects.create(institution=self.inst, name="Núcleo Limeira")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Nucleus.objects.create(institution=self.inst, name="Núcleo Limeira")

    def test_same_nucleus_name_allowed_for_different_institution(self):
        other_inst = Institution.objects.create(
            acronym="IC",
            name="Instituto de Criminalística",
            kind=Institution.Kind.CRIMINALISTICS,
        )

        Nucleus.objects.create(institution=self.inst, name="Núcleo Regional")
        # mesmo nome em outra instituição = permitido
        Nucleus.objects.create(institution=other_inst, name="Núcleo Regional")


class TeamModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.inst = Institution.objects.create(
            acronym="SPTC",
            name="SPTC",
            kind=Institution.Kind.SCIENTIFIC_POLICE,
        )
        cls.nucleus = Nucleus.objects.create(institution=cls.inst, name="Núcleo Limeira")

    def test_unique_team_name_per_nucleus(self):
        Team.objects.create(nucleus=self.nucleus, name="Equipe A")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Team.objects.create(nucleus=self.nucleus, name="Equipe A")

    def test_same_team_name_allowed_for_different_nucleus(self):
        other_nucleus = Nucleus.objects.create(institution=self.inst, name="Núcleo Americana")

        Team.objects.create(nucleus=self.nucleus, name="Equipe 1")
        # mesmo nome em outro núcleo = permitido
        Team.objects.create(nucleus=other_nucleus, name="Equipe 1")


class UserAssignmentConstraintTests(TestCase):
    """
    Testa constraints condicionais:
    - unique_active_team_per_user (end_at IS NULL)
    - unique_active_institution_per_user (end_at IS NULL)
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="TestPass!12345",
        )

        cls.inst = Institution.objects.create(
            acronym="SPTC",
            name="SPTC",
            kind=Institution.Kind.SCIENTIFIC_POLICE,
        )
        cls.city = InstitutionCity.objects.create(institution=cls.inst, name="Limeira", state="SP")
        cls.nucleus = Nucleus.objects.create(institution=cls.inst, name="Núcleo Limeira", city=cls.city)

        cls.team_a = Team.objects.create(nucleus=cls.nucleus, name="Equipe A")
        cls.team_b = Team.objects.create(nucleus=cls.nucleus, name="Equipe B")

        cls.inst2 = Institution.objects.create(
            acronym="PCSP",
            name="Polícia Civil",
            kind=Institution.Kind.CIVIL_POLICE,
        )

    def test_unique_active_team_per_user_blocks_second_active(self):
        UserTeamAssignment.objects.create(user=self.user, team=self.team_a, end_at=None)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserTeamAssignment.objects.create(user=self.user, team=self.team_b, end_at=None)

    def test_unique_active_team_per_user_allows_new_after_closing_previous(self):
        a1 = UserTeamAssignment.objects.create(user=self.user, team=self.team_a, end_at=None)
        a1.end_at = timezone.now()
        a1.save(update_fields=["end_at"])

        # agora pode criar novo ativo
        UserTeamAssignment.objects.create(user=self.user, team=self.team_b, end_at=None)

    def test_unique_active_institution_per_user_blocks_second_active(self):
        UserInstitutionAssignment.objects.create(user=self.user, institution=self.inst, end_at=None)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserInstitutionAssignment.objects.create(user=self.user, institution=self.inst2, end_at=None)

    def test_unique_active_institution_per_user_allows_new_after_closing_previous(self):
        ia1 = UserInstitutionAssignment.objects.create(user=self.user, institution=self.inst, end_at=None)
        ia1.end_at = timezone.now()
        ia1.save(update_fields=["end_at"])

        UserInstitutionAssignment.objects.create(user=self.user, institution=self.inst2, end_at=None)
