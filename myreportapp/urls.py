from django.urls import path

from myreportapp.views import (
    home_view,
    image_editor_view,
    report_dataheader_view,
    report_userreportlist_view,
    report_showreport_view,
    )

urlpatterns = [
    path('', home_view, name='home'),
    path('image_editor/', image_editor_view, name='image_editor'),
    path('report_dataheader/', report_dataheader_view, name='report_dataheader'),
    path('report_dataheader/<int:report_id>/', report_dataheader_view, name='report_dataheader'),
    path('report_showreport_view/<int:report_id>', report_showreport_view, name='report_showreport'),
    path('report_userreportlist', report_userreportlist_view, name='report_userreportlist'),
]
