# myreport/accounts/forms.py

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from institutions.models import Institution, Nucleus, Team
from institutions.models import UserInstitutionAssignment, UserTeamAssignment

from .models import User


class _InstitutionNucleusTeamFieldsMixin(forms.Form):
    """
    Campos auxiliares para vínculo institucional:
    Institution -> Nucleus -> Team
    """

    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all().order_by("name"),
        required=False,
        label="Instituição",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    nucleus = forms.ModelChoiceField(
        queryset=Nucleus.objects.none(),
        required=False,
        label="Núcleo",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        label="Equipe",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def _load_nucleus_queryset(self):
        if "nucleus" not in self.fields:
            return

        institution_id = None
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

        nucleus_id = None
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

    def _set_initial_from_active_assignments(self, user: User):
        """
        Preenche initial a partir das atribuições ativas do usuário.
        Observação: hoje seu código pega institution e team; aqui também inferimos nucleus via team.
        """
        if "institution" not in self.fields or "team" not in self.fields or "nucleus" not in self.fields:
            return

        active_inst = (
            user.institution_assignments.filter(end_at__isnull=True)
            .select_related("institution")
            .order_by("-start_at")
            .first()
        )
        if active_inst:
            self.initial.setdefault("institution", active_inst.institution_id)

        active_team = (
            user.team_assignments.filter(end_at__isnull=True)
            .select_related("team", "team__nucleus", "team__nucleus__institution")
            .order_by("-start_at")
            .first()
        )
        if active_team:
            team_obj = active_team.team
            self.initial.setdefault("team", team_obj.id)
            # núcleo vem do team
            if getattr(team_obj, "nucleus_id", None):
                self.initial.setdefault("nucleus", team_obj.nucleus_id)
            # instituição pode vir do núcleo se não tiver vindo ainda
            if "institution" not in self.initial and getattr(team_obj, "nucleus", None):
                self.initial.setdefault("institution", team_obj.nucleus.institution_id)

    def _clean_institution_nucleus_team_triple(self):
        institution = self.cleaned_data.get("institution")
        nucleus = self.cleaned_data.get("nucleus")
        team = self.cleaned_data.get("team")

        # Regras de completude (se informou um, exige cadeia coerente)
        if any([institution, nucleus, team]) and not all([institution, nucleus, team]):
            if not institution:
                self.add_error("institution", "Selecione uma instituição.")
            if not nucleus:
                self.add_error("nucleus", "Selecione um núcleo.")
            if not team:
                self.add_error("team", "Selecione uma equipe.")
            return institution, nucleus, team

        # Coerência hierárquica
        if institution and nucleus and nucleus.institution_id != institution.id:
            self.add_error("nucleus", "O núcleo selecionado não pertence à instituição informada.")

        if nucleus and team and team.nucleus_id != nucleus.id:
            self.add_error("team", "A equipe selecionada não pertence ao núcleo informado.")

        # (redundante, mas útil) se quiser checar team -> institution também
        if institution and team:
            inst_id = getattr(getattr(team, "nucleus", None), "institution_id", None)
            if inst_id and inst_id != institution.id:
                self.add_error("team", "A equipe selecionada não pertence à instituição informada.")

        return institution, nucleus, team

    def _apply_assignments(self, user: User, institution: Institution, team: Team):
        now = timezone.now()

        UserInstitutionAssignment.objects.filter(user=user, end_at__isnull=True).update(end_at=now)
        UserInstitutionAssignment.objects.create(
            user=user,
            institution=institution,
            start_at=now,
            end_at=None,
            is_primary=True,
        )

        UserTeamAssignment.objects.filter(user=user, end_at__isnull=True).update(end_at=now)
        UserTeamAssignment.objects.create(
            user=user,
            team=team,
            start_at=now,
            end_at=None,
            is_primary=True,
        )

        if not user.can_edit_reports:
            user.can_edit_reports = True
            user.save(update_fields=["can_edit_reports"])


class UserRegistrationForm(_InstitutionNucleusTeamFieldsMixin, UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "email",
            "role",
            "profile_image",
            "background_image",
            "password1",
            "password2",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "background_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # carregamento encadeado
        self._load_nucleus_queryset()
        self._load_team_queryset()

    def clean(self):
        cleaned = super().clean()
        self._clean_institution_nucleus_team_triple()
        return cleaned

    def save(self, commit=True):
        user: User = super().save(commit=commit)

        institution = self.cleaned_data.get("institution")
        team = self.cleaned_data.get("team")

        if institution and team:
            self._apply_assignments(user, institution, team)

        return user


class UserProfileEditForm(_InstitutionNucleusTeamFieldsMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "username",
            "display_name",
            "email",
            "role",
            "profile_image",
            "background_image",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "background_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            initial = kwargs.get("initial", {})
            # reaproveita sua lógica (com nucleus inferido)
            self.initial = initial  # só pra garantir atributo antes
            kwargs["initial"] = initial

        super().__init__(*args, **kwargs)

        if instance:
            self._set_initial_from_active_assignments(instance)

        # carregamento encadeado
        self._load_nucleus_queryset()
        self._load_team_queryset()

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


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password1"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-control"})


class UserSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-control"})


class LinkInstitutionForm(forms.Form):
    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all().order_by("name"),
        label="Instituição",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    nucleus = forms.ModelChoiceField(
        queryset=Nucleus.objects.none(),
        label="Núcleo",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        label="Equipe",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # seta initial (se houver) e prepara querysets
        if not self.is_bound:
            active_inst = (
                user.institution_assignments.filter(end_at__isnull=True)
                .select_related("institution")
                .order_by("-start_at")
                .first()
            )
            active_team = (
                user.team_assignments.filter(end_at__isnull=True)
                .select_related("team", "team__nucleus", "team__nucleus__institution")
                .order_by("-start_at")
                .first()
            )
            if active_inst:
                self.initial.setdefault("institution", active_inst.institution_id)
            if active_team:
                self.initial.setdefault("team", active_team.team_id)
                if active_team.team.nucleus_id:
                    self.initial.setdefault("nucleus", active_team.team.nucleus_id)
                if "institution" not in self.initial:
                    self.initial.setdefault("institution", active_team.team.nucleus.institution_id)

        institution_id = (self.data.get("institution") if self.is_bound else self.initial.get("institution")) or None
        nucleus_id = (self.data.get("nucleus") if self.is_bound else self.initial.get("nucleus")) or None

        if institution_id:
            self.fields["nucleus"].queryset = Nucleus.objects.filter(institution_id=institution_id).order_by("name")
        else:
            self.fields["nucleus"].queryset = Nucleus.objects.none()

        if nucleus_id:
            self.fields["team"].queryset = Team.objects.filter(nucleus_id=nucleus_id).order_by("name")
        else:
            self.fields["team"].queryset = Team.objects.none()

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
        institution: Institution = self.cleaned_data["institution"]
        team: Team = self.cleaned_data["team"]
        now = timezone.now()

        UserInstitutionAssignment.objects.filter(user=self.user, end_at__isnull=True).update(end_at=now)
        UserInstitutionAssignment.objects.create(
            user=self.user,
            institution=institution,
            start_at=now,
            end_at=None,
            is_primary=True,
        )

        UserTeamAssignment.objects.filter(user=self.user, end_at__isnull=True).update(end_at=now)
        UserTeamAssignment.objects.create(
            user=self.user,
            team=team,
            start_at=now,
            end_at=None,
            is_primary=True,
        )

        if not self.user.can_edit_reports:
            self.user.can_edit_reports = True
            self.user.save(update_fields=["can_edit_reports"])
