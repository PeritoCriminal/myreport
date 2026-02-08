# report_maker/forms/cadaver.py
from __future__ import annotations

from common.mixins import BaseModelForm
from report_maker.models import CadaverExamObject


class CadaverExamObjectForm(BaseModelForm):
    class Meta:
        model = CadaverExamObject
        fields = (
            "title",
            "name",
            "description",
            "perinecroscopic_exam",
            "hypostasis",
            "rigor",
            "injuries",
            "clothing",
            "tattoos",
            "body_adornments",
            "observations",
        )
