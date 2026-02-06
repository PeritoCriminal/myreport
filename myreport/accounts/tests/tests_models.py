# accounts/tests/tests_models.py

from __future__ import annotations

from datetime import timedelta
from unittest.mock import PropertyMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone


User = get_user_model()


class UserModelTests(TestCase):
    """
    Testes de model para o app accounts.

    Cobertura focada em:
    - __str__
    - validação (clean) de default_home
    - helpers de path (upload_to)
    - permissões efetivas (create/edit) com mock de vínculo institucional ativo
    """

    def test_str_prefers_display_name_when_present(self) -> None:
        user = User.objects.create_user(username="u1", password="x", display_name="Marcos")
        self.assertEqual(str(user), "Marcos")

    def test_str_falls_back_to_username_when_display_name_empty(self) -> None:
        user = User.objects.create_user(username="u2", password="x", display_name="")
        self.assertEqual(str(user), "u2")

    def test_clean_rejects_invalid_default_home_key(self) -> None:
        user = User(username="u3", default_home="document_list")  # chave inválida
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

    def test_can_edit_reports_effective_requires_flag_and_active_assignment(self) -> None:
        user = User.objects.create_user(username="u7", password="x")
        # flag false => nunca edita
        user.can_edit_reports = False
        user.save()

        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = object()
            self.assertFalse(user.can_edit_reports_effective)

        # flag true + vínculo ativo => edita
        user.can_edit_reports = True
        user.save()

        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = object()
            self.assertTrue(user.can_edit_reports_effective)

        # flag true + sem vínculo => não edita
        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = None
            self.assertFalse(user.can_edit_reports_effective)

    def test_can_create_reports_effective_rules(self) -> None:
        """
        Regras esperadas (modelo atual):
        - can_create_reports precisa estar True
        - precisa haver vínculo institucional ativo
        - se can_create_reports_until for NULL => sem expiração
        - se estiver preenchido => hoje <= until
        """
        user = User.objects.create_user(username="u8", password="x")

        # Se o projeto ainda não tiver esses campos (antes da migração),
        # este teste falharia; por isso fazemos asserts explícitos:
        self.assertTrue(hasattr(user, "can_create_reports"))
        self.assertTrue(hasattr(user, "can_create_reports_until"))
        self.assertTrue(hasattr(user, "can_create_reports_effective"))

        today = timezone.now().date()

        # 1) flag false => não cria
        user.can_create_reports = False
        user.can_create_reports_until = today + timedelta(days=30)
        user.save()

        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = object()
            self.assertFalse(user.can_create_reports_effective)

        # 2) flag true + sem vínculo => não cria
        user.can_create_reports = True
        user.can_create_reports_until = today + timedelta(days=30)
        user.save()

        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = None
            self.assertFalse(user.can_create_reports_effective)

        # 3) flag true + vínculo ativo + until no futuro => cria
        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = object()
            self.assertTrue(user.can_create_reports_effective)

        # 4) flag true + vínculo ativo + until no passado => não cria
        user.can_create_reports_until = today - timedelta(days=1)
        user.save()

        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = object()
            self.assertFalse(user.can_create_reports_effective)

        # 5) flag true + vínculo ativo + until NULL => cria (sem expiração)
        user.can_create_reports_until = None
        user.save()

        with patch.object(User, "active_institution_assignment", new_callable=PropertyMock) as p_active:
            p_active.return_value = object()
            self.assertTrue(user.can_create_reports_effective)
