# report_maker/models/exam_cadaver.py

from __future__ import annotations

from django.db import models

from .exam_base import ExamObject, ExamObjectGroup, RenderBlock


class CadaverExamObject(ExamObject):
    """
    Objeto de exame: Cadáver.

    Campos:
    - title: herdado de ExamObject (ex.: "Cadáver 01", "Cadáver do condutor", etc.)
    - description: herdado de ExamObject (sexo, idade, local/posição, conforme help_text)
    """

    GROUP_KEY = ExamObjectGroup.CADAVERS

    edit_url_name = "report_maker:cadaver_update"
    delete_url_name = "report_maker:cadaver_delete"

    name = models.CharField(
        "Nome",
        max_length=160,
        blank=True,
        help_text="Identificação nominal quando disponível (pode ser ignorado se desconhecido).",
    )

    perinecroscopic_exam = models.TextField(
        "Exame perinecroscópico",
        blank=True,
        default=(
            "Foi realizado exame perinecroscópico do cadáver no local, "
            "com observação externa da posição, indumentária, rigidez cadavérica, "
            "hipóstases, eventuais lesões aparentes e demais características visíveis, "
            "sem a realização de procedimentos invasivos."
        ),
        help_text="Procedimentos adotados no exame externo do cadáver no local.",
    )

    hypostasis = models.TextField(
        "Hipóstases",
        blank=True,
        help_text="Distribuição, coloração e fixidez, quando observadas.",
    )

    injuries = models.TextField(
        "Lesões",
        blank=True,
        help_text="Lesões externas observadas (localização e características objetivas).",
    )

    rigor = models.TextField(
        "Rigidez cadavérica",
        blank=True,
        help_text="Presença e grau/instalação, quando observada.",
    )

    clothing = models.TextField(
        "Indumentária",
        blank=True,
        help_text="Vestuário e condições/posição das peças.",
    )

    tattoos = models.TextField(
        "Tatuagens",
        blank=True,
        help_text="Descrição e localização das tatuagens, quando existentes.",
    )

    body_adornments = models.TextField(
        "Adornos fixados ao corpo",
        blank=True,
        help_text="Ex.: brincos, piercings, anéis, correntes e similares, quando presentes.",
    )

    observations = models.TextField(
        "Observações",
        blank=True,
        help_text="Consignações técnicas complementares.",
    )

    class Meta:
        verbose_name = "Exame de Cadáver"
        verbose_name_plural = "Exames de Cadáver"
        ordering = ("order",)

    @classmethod
    def get_render_blocks(cls) -> list[RenderBlock]:
        return [
            {"kind": "section_field", "label": "Nome", "field": "name", "fmt": "text"},
            {"kind": "section_field", "label": "Descrição", "field": "description", "fmt": "text"},
            {"kind": "section_field", "label": "Indumentária", "field": "clothing", "fmt": "text"},
            {"kind": "section_field", "label": "Tatuagens", "field": "tattoos", "fmt": "text"},
            {"kind": "section_field", "label": "Adornos fixados ao corpo", "field": "body_adornments", "fmt": "text"},
            {"kind": "section_field", "label": "Hipóstases", "field": "hypostasis", "fmt": "text"},
            {"kind": "section_field", "label": "Rigidez cadavérica", "field": "rigor", "fmt": "text"},
            {"kind": "section_field", "label": "Lesões", "field": "injuries", "fmt": "text"},
            {"kind": "section_field", "label": "Observações", "field": "observations", "fmt": "text"},
        ]

    def __str__(self) -> str:
        return self.title or f"Cadáver ({self.pk})"
