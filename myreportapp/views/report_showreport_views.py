from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils.timezone import now
from myreportapp.models import ReportModel

@login_required
def report_showreport_view(request, report_id=None):
    current_user = request.user
    report = None

    if report_id:
        report = get_object_or_404(ReportModel, id=report_id)
        if report.user != current_user:
            raise Http404("Você não tem permissão para acessar este relatório.")
        
        preamble = f'Em {report.designation_date}, foi o {report.expert_display_name}.'
    context = {
        'report_number': report.report_number,
        'preamble': preamble,
    }
    
    return render(request, 'report_showreport.html', context)