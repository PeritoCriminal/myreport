from __future__ import annotations

from common.mixins import BaseModelForm

from report_maker.models.exam_public_road import PublicRoadExamObject


class PublicRoadExamObjectForm(BaseModelForm):
    class Meta:
        model = PublicRoadExamObject
        fields = (
            "title",
            "geo_location",
            "description",
            "weather_conditions",
            "road_conditions",
            "traffic_signage",
            "observed_elements",
        )
