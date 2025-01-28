from django.urls import path

from myreportapp.views import (
    home_view,
    image_editor_view,
    report_dataheader_view,
    report_userreportlist_view,
    report_showreport_view,
    report_policereport_view,
    report_requestauthority_view,
    report_preservation_view,
    )

urlpatterns = [
    path('', home_view, name='home'),
    path('image_editor/', image_editor_view, name='image_editor'),
    path('report_dataheader/', report_dataheader_view, name='report_dataheader'),
    path('report_dataheader/<int:report_id>/', report_dataheader_view, name='report_dataheader'),
    path('report_showreport/<int:report_id>', report_showreport_view, name='report_showreport'),
    path('report_userreportlist', report_userreportlist_view, name='report_userreportlist'),
    path('report_datapolicereport/<int:report_id>', report_policereport_view, name='report_datapolicereport'),
    path('report_datarequest/<int:report_id>', report_requestauthority_view, name='report_datarequest'),
    path('report_preservation/<int:report_id>',report_preservation_view, name='report_preservation_new'),
    path('report_preservation/<int:report_id>/<int:preservation_id>/',report_preservation_view, name='report_preservation_edit'),
    ]
