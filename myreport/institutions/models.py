# institutions/models.py

from django.conf import settings
from django.db import models


class FederationUnit(models.Model):
    """
    UF (SP, RJ, MG...), para permitir expansão nacional.
    """
    code = models.CharField(max_length=2, unique=True)   # "SP"
    name = models.CharField(max_length=64)               # "São Paulo"

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Institution(models.Model):
    """
    Órgão/Instituição (ex.: Secretaria de Segurança Pública do Estado de SP,
    Polícia Científica do PR, etc.)
    """
    uf = models.ForeignKey(FederationUnit, on_delete=models.PROTECT, related_name="institutions")
    name = models.CharField(max_length=160)              # "Secretaria da Segurança Pública do Estado de São Paulo"
    short_name = models.CharField(max_length=80, blank=True)  # "SSP-SP" (opcional)

    class Meta:
        unique_together = [("uf", "name")]
        ordering = ["uf__code", "name"]

    def __str__(self):
        return self.short_name or self.name


class ForensicAgency(models.Model):
    """
    Unidade técnica (ex.: Instituto de Criminalística, IML, etc.)
    """
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name="agencies")
    name = models.CharField(max_length=160)              # "Instituto de Criminalística"
    city = models.CharField(max_length=80, blank=True)   # pode ficar aqui ou no 'WorkUnit' (depende do seu caso)
    superintendent_name = models.CharField(max_length=120, blank=True)  # "Dr. Fulano"

    class Meta:
        unique_together = [("institution", "name", "city")]
        ordering = ["institution__uf__code", "name", "city"]

    def __str__(self):
        return self.name


class WorkUnit(models.Model):
    """
    Unidade/Equipe local (Núcleo, Seção, Equipe etc.).
    """
    agency = models.ForeignKey(ForensicAgency, on_delete=models.PROTECT, related_name="work_units")
    name = models.CharField(max_length=160)              # "Núcleo de Perícias de Santos" / "Equipe Plantão"
    city = models.CharField(max_length=80, blank=True)   # se preferir granular aqui

    class Meta:
        unique_together = [("agency", "name")]
        ordering = ["agency__name", "name"]

    def __str__(self):
        return self.name


class InstitutionalProfile(models.Model):
    """
    1:1 com o usuário: “local de trabalho” atual.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institutional_profile",
    )
    work_unit = models.ForeignKey(WorkUnit, on_delete=models.PROTECT, null=True, blank=True)
    examiner_display_name = models.CharField(max_length=120, blank=True)  # se quiser travar “Dr./Dra.” por aqui
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.work_unit or 'sem unidade'}"
