# path: myreport/accounts/tests/tests_models.py

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from institutions.models import Institution, Nucleus, Team


User = get_user_model()


class UserModelTests(TestCase):
    """
    Testes de model para o app accounts.

    Cobertura focada em:
    - __str__
    - validação (clean) de default_home
    - helpers de path (upload_to)
    - permissões efetivas (create/edit) no modelo simplificado (via user.team)
    """

    def _create_team(self):
        inst = Institution.objects.create(name="Inst", acronym="I")
        nucleus = Nucleus.objects.create(name="Nuc", institution=inst)
        team = Team.objects.create(name="Team A", nucleus=nucleus)
        return team

    def test_str_prefers_display_name_when_present(self) -> None:
        user = User.objects.create_user(username="u1", password="x", display_name="Marcos")
        self.assertEqual(str(user), "Marcos")

    def test_str_falls_back_to_username_when_display_name_empty(self) -> None:
        user = User.objects.create_user(username="u2", password="x", display_name="")
        self.assertEqual(str(user), "u2")

    def test_clean_rejects_invalid_default_home_key(self) -> None:
        user = User(username="u3", default_home="document_list")
        with self.assertRaises(ValidationError) as ctx:
            user.full_clean()

        self.assertIn("default_home", ctx.exception.message_dict)

    def test_clean_accepts_valid_default_home_key(self) -> None:
        user = User.objects.create_user(
            username="u4",
            password="x",
            default_home=getattr(User, "HOME_DASHBOARD", "dashboard"),
        )
        user.full_clean()

    def test_user_profile_image_path(self) -> None:
        from accounts.models import user_profile_image_path

        user = User.objects.create_user(username="u5", password="x")
        path = user_profile_image_path(user, "photo.jpg")
        self.assertTrue(path.endswith("/profile/photo.jpg"))
        self.assertIn(str(user.id), path)

    def test_user_background_image_path(self) -> None:
        from accounts.models import user_background_image_path

        user = User.objects.create_user(username="u6", password="x")
        path = user_background_image_path(user, "bg.png")
        self.assertTrue(path.endswith("/background/bg.png"))
        self.assertIn(str(user.id), path)

    # ---------------------------------------------------------
    # Permissões efetivas (modelo simplificado)
    # ---------------------------------------------------------

    def test_can_edit_reports_effective_requires_flag_and_team(self) -> None:
        user = User.objects.create_user(username="u7", password="x")

        team = self._create_team()

        # flag false => nunca edita
        user.can_edit_reports = False
        user.team = team
        user.save()

        self.assertFalse(user.can_edit_reports_effective)

        # flag true + team => edita
        user.can_edit_reports = True
        user.save()

        self.assertTrue(user.can_edit_reports_effective)

        # flag true + sem team => não edita
        user.team = None
        user.save()

        self.assertFalse(user.can_edit_reports_effective)

    def test_can_create_reports_effective_rules(self) -> None:
        """
        Regras esperadas:
        - can_create_reports precisa estar True
        - precisa haver team definido
        - se can_create_reports_until for NULL => sem expiração
        - se estiver preenchido => hoje <= until
        """
        user = User.objects.create_user(username="u8", password="x")
        team = self._create_team()

        today = timezone.now().date()

        # 1) flag false => não cria
        user.can_create_reports = False
        user.can_create_reports_until = today + timedelta(days=30)
        user.team = team
        user.save()

        self.assertFalse(user.can_create_reports_effective)

        # 2) flag true + sem team => não cria
        user.can_create_reports = True
        user.team = None
        user.can_create_reports_until = today + timedelta(days=30)
        user.save()

        self.assertFalse(user.can_create_reports_effective)

        # 3) flag true + team + until futuro => cria
        user.team = team
        user.can_create_reports_until = today + timedelta(days=30)
        user.save()

        self.assertTrue(user.can_create_reports_effective)

        # 4) flag true + team + until passado => não cria
        user.can_create_reports_until = today - timedelta(days=1)
        user.save()

        self.assertFalse(user.can_create_reports_effective)

        # 5) flag true + team + until NULL => cria
        user.can_create_reports_until = None
        user.save()

        self.assertTrue(user.can_create_reports_effective)