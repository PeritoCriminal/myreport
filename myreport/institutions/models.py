# institutions/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class Institution(models.Model):
    """
    Institution (public body / organization) that participates in the system.

    Notes:
    - We keep a SINGLE table for all institutions.
    - Specific differences can be handled later via `kind`
      and/or OneToOne profile models.
    """

    class Kind(models.TextChoices):
        SCIENTIFIC_POLICE = "SCIENTIFIC_POLICE", "Polícia Técnico-Científica"
        CIVIL_POLICE = "CIVIL_POLICE", "Polícia Civil"
        MEDICAL_LEGAL = "MEDICAL_LEGAL", "Instituto Médico-Legal"
        CRIMINALISTICS = "CRIMINALISTICS", "Instituto de Criminalística"
        OTHER = "OTHER", "Outro"

    acronym = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)

    kind = models.CharField(
        max_length=40,
        choices=Kind.choices,
        default=Kind.OTHER,
    )

    director_name = models.CharField(max_length=255, blank=True, default="")
    director_title = models.CharField(max_length=255, blank=True, default="")

    # in honor of / emblems / coats of arms
    honoree_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Título honorífico (ex.: Perito Criminal Dr.)"
    )
    honoree_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nome do patrono ou homenageado institucional"
    )

    emblem_primary = models.ImageField(
        upload_to="institutions/emblems/", blank=True, null=True
    )
    emblem_secondary = models.ImageField(
        upload_to="institutions/emblems/", blank=True, null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Institution"
        verbose_name_plural = "Institutions"
        ordering = ["acronym"]

    def __str__(self) -> str:
        return f"{self.acronym} - {self.name}"

    @property
    def header(self) -> dict:
        """
        Standardized header payload for HTML / PDF / DOCX rendering.
        """
        honoree = None
        if self.honoree_name:
            if self.honoree_title:
                honoree = f'{self.honoree_title} {self.honoree_name}'
            else:
                honoree = self.honoree_name

        return {
            "acronym": self.acronym,  # Ex.: SPTC
            "name": self.name,        # Superintendência da Polícia Técnico-Científica (SPTC)
            "honoree": honoree,       # Ex.: PERITO CRIMINAL DR. OCTÁVIO EDUARDO DE BRITO ALVARENGA
            "emblem_primary": self.emblem_primary,
            "emblem_secondary": self.emblem_secondary,
            "kind": self.kind,        # não renderiza, só lógica
        }


class InstitutionCity(models.Model):
    """
    Cities where an Institution operates.

    Kept as a standalone model to avoid coupling with external apps.
    Can be replaced by a FK to common.City later if desired.
    """

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="cities",
    )

    name = models.CharField(max_length=120)
    state = models.CharField(max_length=2, default="SP")

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Institution City"
        verbose_name_plural = "Institution Cities"
        ordering = ["institution__acronym", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name", "state"],
                name="unique_city_per_institution",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}/{self.state} ({self.institution.acronym})"


class Nucleus(models.Model):
    """
    Regional nucleus (unit) of an Institution.
    """

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="nuclei",
    )

    name = models.CharField(max_length=255)

    city = models.ForeignKey(
        InstitutionCity,
        on_delete=models.PROTECT,
        related_name="nuclei",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Nucleus"
        verbose_name_plural = "Nuclei"
        ordering = ["institution__acronym", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name"],
                name="unique_nucleus_name_per_institution",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.institution.acronym})"


class Team(models.Model):
    """
    Team linked to a Nucleus.
    """

    nucleus = models.ForeignKey(
        Nucleus,
        on_delete=models.CASCADE,
        related_name="teams",
    )

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        ordering = [
            "nucleus__institution__acronym",
            "nucleus__order",
            "order",
            "name",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["nucleus", "name"],
                name="unique_team_name_per_nucleus",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.nucleus.name} / {self.nucleus.institution.acronym})"


class UserTeamAssignment(models.Model):
    """
    Historical assignment of a user to a Team.
    A user may have many assignments over time,
    but only ONE active assignment at a time.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_assignments",
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="team_assignments",
    )

    start_at = models.DateTimeField(default=timezone.now, db_index=True)
    end_at = models.DateTimeField(blank=True, null=True, db_index=True)

    is_primary = models.BooleanField(
        default=True,
        help_text="Defines whether this is the user's primary team for the period.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Team Assignment"
        verbose_name_plural = "User Team Assignments"
        ordering = ["-start_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(end_at__isnull=True),
                name="unique_active_team_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "end_at"]),
        ]

    def __str__(self):
        status = "active" if self.end_at is None else "closed"
        return f"{self.user} → {self.team} ({status})"


class UserInstitutionAssignment(models.Model):
    """
    Historical assignment of a user to an Institution.
    A user may have many assignments over time,
    but only ONE active assignment at a time.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institution_assignments",
    )

    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="institution_assignments",
    )

    start_at = models.DateTimeField(default=timezone.now, db_index=True)
    end_at = models.DateTimeField(blank=True, null=True, db_index=True)

    is_primary = models.BooleanField(
        default=True,
        help_text="Defines whether this is the user's primary institution for the period.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Institution Assignment"
        verbose_name_plural = "User Institution Assignments"
        ordering = ["-start_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(end_at__isnull=True),
                name="unique_active_institution_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "end_at"]),
        ]

    def __str__(self):
        status = "active" if self.end_at is None else "closed"
        return f"{self.user} → {self.institution.acronym} ({status})"
