# report_maker/models/mixins.py

from __future__ import annotations
from django.db import models


class HasMethodologyMixin(models.Model):
    """
    Adiciona campo de metodologia ao objeto de exame.

    Utilizado por objetos cuja análise envolve procedimento técnico
    ou método pericial explicitável.
    """
    methodology = models.TextField(
        "Metodologia",
        blank=True,
    )

    class Meta:
        abstract = True


class HasResultsMixin(models.Model):
    """
    Adiciona campo de resultados ao objeto de exame.

    Utilizado quando o exame gera constatações objetivas
    ou conclusões parciais específicas do objeto.
    """
    results = models.TextField(
        "Resultados",
        blank=True,
    )

    class Meta:
        abstract = True


class HasServiceContextMixin(models.Model):
    """
    Adiciona campo de contexto do atendimento pericial.

    Destina-se ao registro de informações circunstanciais do atendimento,
    como preservação do local, presença da autoridade requisitante,
    isolamento, intervenções prévias, entre outros dados relevantes.
    """
    service_context = models.TextField(
        "Contexto do atendimento",
        blank=True,
        help_text=(
            "Informações sobre preservação do local, presença da autoridade "
            "requisitante, isolamento, intervenções prévias etc."
        ),
    )

    class Meta:
        abstract = True



class HasObservedElementsMixin(models.Model):
    """
    Placeholder para 'Elementos Observados'.

    A ideia é este mixin virar o “container padrão” dos vestígios/achados
    do exame (marcas, danos, manchas, etc.), possivelmente de forma estruturada
    (ex.: tabela relacionada, json, ou blocos ordenáveis).
    """
    observed_elements = models.TextField(
        "Elementos Observados",
        blank=True,
    )

    class Meta:
        abstract = True