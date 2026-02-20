# path: myreport/institutions/tests/tests_model.py

from django.db import IntegrityError, transaction
from django.test import TestCase

from institutions.models import (
    Institution,
    InstitutionCity,
    Nucleus,
    Team,
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
        Team.objects.create(nucleus=other_nucleus, name="Equipe 1")