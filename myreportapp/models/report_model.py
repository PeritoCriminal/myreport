#newreportapp/models/report_model.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date

class ReportModel(models.Model):
    """ A classe ReportModel tem atributos e métdodos comuns a todos os relatórios """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário"
    )

    # Dados do usuário
    expert_display_name = models.CharField('Perito', max_length=200, default='')
    institute_director = models.CharField('Diretor do Instituto', max_length=200, default='')
    institute_unit = models.CharField('Núcleo do Instituto', max_length=200, default='')
    forensic_team_base = models.CharField('Base da Equipe de Perícias', max_length=200, default='')

    # Dados do atendimento
    report_number = models.CharField('Número do Laudo', max_length=100, default='', null=True)
    protocol_number = models.CharField('Número do Protocolo', max_length=200, default='', null=True)
    report_date = models.DateField('Data do Registro', auto_now_add=True) 
    updated_at = models.DateTimeField('Data de Atualização', auto_now=True)
    designation_date = models.DateField('Data de Designação', default=timezone.localdate)
    service_date = models.DateField('Data do Atendimento', default=timezone.localdate) 
    service_time = models.TimeField('Hora do Atendimento', null=True, default='00:00:00')
    photographer = models.CharField('Fotografia', max_length=200, default='') 
    considerations = models.TextField('Considerações', blank=True, default='')
    conclusion = models.TextField('Conclusão', blank=True, default='')   

    # Dados do Boletim de Ocorrência 
    has_police_report = models.BooleanField('Elaborado Boletim?', default=False)
    police_report_number = models.CharField('Número do Boletim de Ocorrência', max_length=200, default='', null=True)
    police_station = models.CharField('Distrito Policial', max_length=200, default='', null=True)
    occurrence_date = models.DateField('Data da Ocorrência', default=timezone.localdate) 
    occurrence_time = models.TimeField('Hora do Atendimento', null=True, default='00:00:00')
    city = models.CharField('Cidade', max_length=100, default='Limeira', null=True)
    incident_nature = models.CharField('Natureza da Ocorrência', max_length=300, default='', null=True)    

    # Dados da requisição de Exame
    has_authority_request = models.BooleanField('Requistado?', default=False)
    requesting_authority = models.CharField('Autoridade Requisitante', max_length=200, default='', null=True)
    call_date = models.DateField('Data do Acionamento', default=timezone.localdate) 
    call_time = models.TimeField('Hora do Acionamento', null=True, default='00:00:00')
    examination_objective = models.CharField('Objetivo do Exame', max_length=300, default='')      

    class Meta:
        verbose_name = 'Relatório Pericial'
        verbose_name_plural = 'Relatórios Periciais'
        ordering = ['-updated_at']
