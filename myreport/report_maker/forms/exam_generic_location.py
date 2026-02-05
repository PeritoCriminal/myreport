from __future__ import annotations

from common.mixins import BaseModelForm

from report_maker.models import GenericLocationExamObject


class GenericLocationExamObjectForm(BaseModelForm):
    class Meta:
        model = GenericLocationExamObject
        fields = (
            "title",
            "geo_location",
            "service_context",
            "description",
            "observed_elements",
        )
