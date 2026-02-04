# report_maker/forms/vehicle_inspection.py

from django import forms
from report_maker.models.exam_vehicle_inspection import VehicleInspectionExamObject


class VehicleInspectionExamObjectForm(forms.ModelForm):
    class Meta:
        model = VehicleInspectionExamObject
        fields = (
            "title",
            "description",
            "methodology_kind",
            "methodology",
            "observed_elements",
            "operational_tests",
            "tire_conditions",
            "optional_notes",
        )
