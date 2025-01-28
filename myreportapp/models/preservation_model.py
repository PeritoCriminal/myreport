from django.db import models

class PreservationModel(models.Model):
    # Atributos principais
    preservation_team = models.CharField(max_length=255, verbose_name="Equipe de Preservação")
    officer_in_charge = models.CharField(max_length=255, verbose_name="Encarregado")
    official_vehicle = models.CharField(max_length=100, verbose_name="Viatura", blank=True, null=True)
    preservation_conditions = models.TextField(verbose_name="Condições de Preservação")
    police_authority_present = models.BooleanField(verbose_name="Autoridade Policial Presente", default=False)
    investigation_team_present = models.BooleanField(verbose_name="Equipe de Investigação Presente", default=False)
    general_context = models.TextField(verbose_name="Contexto Geral")

    # Relacionamento com ReportModel
    report = models.ForeignKey(
        'ReportModel', 
        on_delete=models.CASCADE, 
        related_name='preservations',
        verbose_name="Relatório"
    )

    # Atributos de praxe
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    # Configurações adicionais
    class Meta:
        verbose_name = "Preservação"
        verbose_name_plural = "Preservações"

    def __str__(self):
        return f"Preservação - {self.preservation_team} ({self.created_at.strftime('%d/%m/%Y')})"
