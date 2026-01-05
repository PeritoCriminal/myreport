from django.db import models

from .exam_base import ExamObject


class GenericExamObject(ExamObject):
    """
    Objeto de exame genérico, utilizado quando o elemento periciado
    não se enquadra em uma tipificação específica.
    """

    class Meta:
        verbose_name = "Objeto genérico"
        verbose_name_plural = "Objetos genéricos"

    def __str__(self):
        return self.title or f"Objeto genérico ({self.pk})"
