# institutions/models.py
from django.db import models


class Institution(models.Model):
    """
    Instituição (órgão) que participa do sistema.

    Observação:
    - Mantemos UMA tabela única para todas as instituições.
    - Diferenças específicas podem ser tratadas por `kind` e/ou por um perfil OneToOne no futuro.
    """

    class Kind(models.TextChoices):
        SPTC_SP = "SPTC_SP", "SPTC (SP)"
        POLICIA_CIENTIFICA = "POLICIA_CIENTIFICA", "Polícia Científica"
        POLICIA_CIVIL = "POLICIA_CIVIL", "Polícia Civil"
        OUTRA = "OUTRA", "Outra"

    sigla = models.CharField(max_length=30, unique=True)
    nome = models.CharField(max_length=255)

    kind = models.CharField(max_length=40, choices=Kind.choices, default=Kind.OUTRA)

    diretor_nome = models.CharField(max_length=255, blank=True, default="")
    diretor_cargo = models.CharField(max_length=255, blank=True, default="")

    # Imagens (brasões)
    brasao_1 = models.ImageField(upload_to="institutions/brasoes/", blank=True, null=True)
    brasao_2 = models.ImageField(upload_to="institutions/brasoes/", blank=True, null=True)

    # Ativação lógica
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Instituição"
        verbose_name_plural = "Instituições"
        ordering = ["sigla"]

    def __str__(self) -> str:
        return f"{self.sigla} - {self.nome}"

    @property
    def header(self) -> dict:
        """
        Retorna um 'pacote' padronizado para cabeçalho (HTML/PDF/DOCX).
        Você pode consumir isso direto no gerador de documentos.
        """
        return {
            "sigla": self.sigla,
            "nome": self.nome,
            "diretor_nome": self.diretor_nome,
            "diretor_cargo": self.diretor_cargo,
            "brasao_1": self.brasao_1,
            "brasao_2": self.brasao_2,
            "kind": self.kind,
        }


class InstitutionCity(models.Model):
    """
    Cidades de atuação/abrangência da Instituição.

    Mantive como tabela própria (e não ManyToMany para um model City externo)
    para não te amarrar a outro app agora.
    Se você já tem um common.City, pode trocar este model por FK.
    """

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="cities"
    )
    name = models.CharField(max_length=120)
    state = models.CharField(max_length=2, default="SP")  # UF (ex.: SP, RJ...)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Cidade da Instituição"
        verbose_name_plural = "Cidades da Instituição"
        ordering = ["institution__sigla", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "name", "state"],
                name="unique_city_per_institution",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}/{self.state} ({self.institution.sigla})"


class Nucleo(models.Model):
    """
    Núcleo (unidade regional) de uma Instituição.
    """

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="nucleos"
    )
    nome = models.CharField(max_length=255)

    cidade = models.ForeignKey(
        InstitutionCity,
        on_delete=models.PROTECT,
        related_name="nucleos",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Núcleo"
        verbose_name_plural = "Núcleos"
        ordering = ["institution__sigla", "order", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "nome"],
                name="unique_nucleo_name_per_institution",
            )
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.institution.sigla})"


class Equipe(models.Model):
    """
    Equipe vinculada a um Núcleo.
    """

    nucleo = models.ForeignKey(Nucleo, on_delete=models.CASCADE, related_name="equipes")
    nome = models.CharField(max_length=255)

    # Campo opcional: ex.: "Equipe de Local", "Equipe de Balística" etc.
    descricao = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"
        ordering = ["nucleo__institution__sigla", "nucleo__order", "order", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["nucleo", "nome"],
                name="unique_equipe_name_per_nucleo",
            )
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.nucleo.nome} / {self.nucleo.institution.sigla})"
