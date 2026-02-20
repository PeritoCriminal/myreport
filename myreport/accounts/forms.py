# myreport/accounts/forms.py
from __future__ import annotations

# ─────────────────────────────────────
# Django
# ─────────────────────────────────────
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordChangeForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.utils import timezone

# ─────────────────────────────────────
# Apps do projeto
# ─────────────────────────────────────
from .home_registry import get_allowed_home_choices, get_home_keys
from institutions.models import (
    Institution,
    Nucleus,
    Team,
)

# ─────────────────────────────────────
# Comum / Mixins
# ─────────────────────────────────────
from common.mixins import BaseForm, BaseModelForm, BootstrapFormMixin


User = get_user_model()


class _InstitutionNucleusTeamFieldsMixin(BaseForm):
    """
    Campos auxiliares para vínculo institucional:
    Institution -> Nucleus -> Team
    """

    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all().order_by("name"),
        required=False,
        label="Instituição",
        # sem widget.attrs aqui (BaseForm aplica)
    )

    nucleus = forms.ModelChoiceField(
        queryset=Nucleus.objects.none(),
        required=False,
        label="Núcleo",
    )

    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        label="Equipe",
    )

    def _load_nucleus_queryset(self):
        if "nucleus" not in self.fields:
            return

        if self.is_bound:
            institution_id = self.data.get("institution") or None
        else:
            institution_id = self.initial.get("institution") or None

        if institution_id:
            self.fields["nucleus"].queryset = (
                Nucleus.objects.filter(institution_id=institution_id).order_by("name")
            )
        else:
            self.fields["nucleus"].queryset = Nucleus.objects.none()

    def _load_team_queryset(self):
        if "team" not in self.fields:
            return

        if self.is_bound:
            nucleus_id = self.data.get("nucleus") or None
        else:
            nucleus_id = self.initial.get("nucleus") or None

        if nucleus_id:
            self.fields["team"].queryset = (
                Team.objects.filter(nucleus_id=nucleus_id)
                .select_related("nucleus", "nucleus__institution")
                .order_by("name")
            )
        else:
            self.fields["team"].queryset = Team.objects.none()

    def _set_initial_from_active_assignments(self, user):
        """
        Preenche initial a partir da equipe atual do usuário (modelo simplificado).
        """
        if (
            "institution" not in self.fields
            or "team" not in self.fields
            or "nucleus" not in self.fields
        ):
            return

        team = user.team
        if not team:
            return

        self.initial.setdefault("team", team.id)
        if team.nucleus_id:
            self.initial.setdefault("nucleus", team.nucleus_id)
            if team.nucleus.institution_id:
                self.initial.setdefault("institution", team.nucleus.institution_id)


    def _clean_institution_nucleus_team_triple(self):
        institution = self.cleaned_data.get("institution")
        nucleus = self.cleaned_data.get("nucleus")
        team = self.cleaned_data.get("team")

        if any([institution, nucleus, team]) and not all([institution, nucleus, team]):
            if not institution:
                self.add_error("institution", "Selecione uma instituição.")
            if not nucleus:
                self.add_error("nucleus", "Selecione um núcleo.")
            if not team:
                self.add_error("team", "Selecione uma equipe.")
            return institution, nucleus, team

        if institution and nucleus and nucleus.institution_id != institution.id:
            self.add_error("nucleus", "O núcleo selecionado não pertence à instituição informada.")

        if nucleus and team and team.nucleus_id != nucleus.id:
            self.add_error("team", "A equipe selecionada não pertence ao núcleo informado.")

        if institution and team:
            inst_id = getattr(getattr(team, "nucleus", None), "institution_id", None)
            if inst_id and inst_id != institution.id:
                self.add_error("team", "A equipe selecionada não pertence à instituição informada.")

        return institution, nucleus, team

    def _apply_assignments(self, user, institution: Institution, team: Team):
        """
        No modelo simplificado, apenas define a equipe do usuário.
        A instituição é inferida via team -> nucleus -> institution.
        """
        user.team = team

        if not user.can_edit_reports:
            user.can_edit_reports = True

        user.save(update_fields=["team", "can_edit_reports"])



class UserRegistrationForm(_InstitutionNucleusTeamFieldsMixin, UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "report_signature_name",
            "email",
            "role",
            "profile_image",
            "background_image",
            "password1",
            "password2",
        )
        # widgets removidos: BaseForm aplica classes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ IMPORTANTE: em POST, o Django só valida se o valor estiver no queryset.
        # Então ajustamos os querysets com base em self.data (form submit) ou self.initial.
        self._load_nucleus_queryset()
        self._load_team_queryset()

        # aplica bootstrap também nos campos extras do UserCreationForm
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        self._clean_institution_nucleus_team_triple()
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=commit)

        institution = self.cleaned_data.get("institution")
        team = self.cleaned_data.get("team")

        if institution and team:
            self._apply_assignments(user, institution, team)

        return user


class UserProfileEditForm(_InstitutionNucleusTeamFieldsMixin, BaseModelForm):
    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "report_signature_name",
            "email",
            "role",
            "profile_image",
            "background_image",
        )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")

        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields["username"].widget.attrs["readonly"] = True

        # ✅ Edit: preenche institution/nucleus/team a partir da atribuição ativa
        if instance:
            self._set_initial_from_active_assignments(instance)

        # ✅ IMPORTANTE: depois de definir initial (no edit),
        # carregamos os querysets encadeados para exibir e validar corretamente.
        self._load_nucleus_queryset()
        self._load_team_queryset()

    def clean(self):
        cleaned = super().clean()
        self._clean_institution_nucleus_team_triple()
        return cleaned

    def save(self) -> None:
        team: Team = self.cleaned_data["team"]

        self.user.team = team

        if not self.user.can_edit_reports:
            self.user.can_edit_reports = True

        self.user.save(update_fields=["team", "can_edit_reports"])



class UserPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    pass


class UserSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass


class LinkInstitutionForm(_InstitutionNucleusTeamFieldsMixin):
    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all().order_by("name"),
        label="Instituição",
        required=True,
    )
    nucleus = forms.ModelChoiceField(
        queryset=Nucleus.objects.none(),
        label="Núcleo",
        required=True,
    )
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        label="Equipe",
        required=True,
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if not self.is_bound:
            team = user.team
            if team:
                self.initial.setdefault("team", team.id)
                self.initial.setdefault("nucleus", team.nucleus_id)
                self.initial.setdefault("institution", team.nucleus.institution_id)

        institution_id = (
            (self.data.get("institution") if self.is_bound else self.initial.get("institution")) or None
        )
        nucleus_id = (self.data.get("nucleus") if self.is_bound else self.initial.get("nucleus")) or None

        if institution_id:
            self.fields["nucleus"].queryset = Nucleus.objects.filter(institution_id=institution_id).order_by("name")
        else:
            self.fields["nucleus"].queryset = Nucleus.objects.none()

        if nucleus_id:
            self.fields["team"].queryset = Team.objects.filter(nucleus_id=nucleus_id).order_by("name")
        else:
            self.fields["team"].queryset = Team.objects.none()

        # aplica bootstrap (inclui selects)
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        institution = cleaned.get("institution")
        nucleus = cleaned.get("nucleus")
        team = cleaned.get("team")

        if nucleus and institution and nucleus.institution_id != institution.id:
            raise ValidationError("O núcleo selecionado não pertence à instituição informada.")
        if team and nucleus and team.nucleus_id != nucleus.id:
            raise ValidationError("A equipe selecionada não pertence ao núcleo informado.")
        return cleaned

    def save(self) -> None:
        team: Team = self.cleaned_data["team"]

        self.user.team = team

        if not self.user.can_edit_reports:
            self.user.can_edit_reports = True

        self.user.save(update_fields=["team", "can_edit_reports"])


# ─────────────────────────────────────
# Preferências do usuário
# ─────────────────────────────────────
class UserPreferencesForm(BaseModelForm):
    """
    Form de preferências do usuário.

    Observação:
    - nucleus/team NÃO são campos do User; são preferências operacionais.
    - o vínculo institucional é inferido por User.team (modelo simplificado).
    """

    nucleus = forms.ModelChoiceField(
        queryset=Nucleus.objects.filter(is_active=True).order_by("name"),
        required=True,
        label="Núcleo",
    )
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        label="Equipe",
        help_text="Se não selecionar uma equipe, será utilizada a equipe correspondente ao próprio núcleo.",
    )

    class Meta:
        model = User
        fields = (
            "theme",
            "default_home",
            "closing_phrase",
        )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user or self.instance

        # choices de default_home (com base no registro/flags do projeto)
        if "default_home" in self.fields:
            allowed = get_allowed_home_choices(self.user)
            # allowed pode vir como list[tuple] ou dict; garantimos list[tuple]
            if isinstance(allowed, dict):
                allowed = list(allowed.items())
            self.fields["default_home"].choices = allowed

        # initial: assignment ativo (team -> nucleus)
        team = self.user.team
        if team:
            self.fields["nucleus"].initial = team.nucleus_id
            self.fields["team"].initial = team.id


        # queryset encadeado de teams (POST ou initial)
        nucleus_id = None
        if self.is_bound:
            nucleus_id = self.data.get("nucleus") or None
        else:
            nucleus_id = self.fields["nucleus"].initial or None

        if nucleus_id:
            self.fields["team"].queryset = (
                Team.objects.filter(nucleus_id=nucleus_id, is_active=True)
                .order_by("order", "name")
            )
        else:
            self.fields["team"].queryset = Team.objects.none()

        # aplica bootstrap também nos campos adicionados manualmente (nucleus/team)
        self.apply_bootstrap()

    def clean(self):
        cleaned = super().clean()
        nucleus: Nucleus | None = cleaned.get("nucleus")
        team: Team | None = cleaned.get("team")

        if team and nucleus and team.nucleus_id != nucleus.id:
            self.add_error("team", "A equipe selecionada não pertence ao núcleo informado.")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=commit)

        nucleus: Nucleus = self.cleaned_data["nucleus"]
        team: Team | None = self.cleaned_data.get("team")

        # Se não escolheu equipe, usa (ou cria) a “equipe do núcleo”
        if not team:
            team, _ = Team.objects.get_or_create(
                nucleus=nucleus,
                is_nucleus_team=True,
                defaults={"name": nucleus.name, "is_active": True, "order": 0},
            )

        user.team = team

        if not user.can_edit_reports:
            user.can_edit_reports = True

        user.save(update_fields=["team", "can_edit_reports"])
        return user
