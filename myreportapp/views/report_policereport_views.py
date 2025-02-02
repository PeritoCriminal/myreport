from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.timezone import now
from django.urls import reverse
from myreportapp.models import ReportModel

@login_required
def report_policereport_view(request, report_id=None):  # Sempre terá um ID
    current_user = request.user
    report = get_object_or_404(ReportModel, id=report_id)

    # Verifica se o relatório pertence ao usuário logado
    if report.user != current_user:
        raise Http404("Você não tem permissão para acessar este relatório.")

    if request.method == 'POST':
        section_police_report = request.POST.get('section_police_report', '').strip()
        police_report_number = request.POST.get('police_report_number', '').strip()
        police_station = request.POST.get('police_station', '').strip()
        incident_nature = request.POST.get('incident_nature', '').strip()
        occurrence_date = request.POST.get('occurrence_date', now().date())
        occurrence_time = request.POST.get('occurrence_time', '00:00:00')

        # Atualiza os dados do relatório
        report.has_police_report = True
        report.section_police_report = section_police_report
        report.police_report_number = police_report_number
        report.police_station = police_station
        report.incident_nature = incident_nature
        report.occurrence_date = occurrence_date
        report.occurrence_time = occurrence_time
        report.save()
        return redirect(reverse('report_showreport', kwargs={'report_id': report.id}))

    # Contexto para renderização inicial da página
    context = {
        'report_id': report.id,
        'section_police_report': report.section_police_report if report else '',
        'police_report_number': report.police_report_number if report else '',
        'police_station': report.police_station if report else '',
        'incident_nature': report.incident_nature if report else '',
        'designation_date': report.designation_date.isoformat() if report and report.designation_date else now().date().isoformat(),
        'occurrence_date': report.occurrence_date.isoformat() if report and report.occurrence_date else now().date().isoformat(),
        'occurrence_time': report.occurrence_time.strftime('%H:%M') if report and report.occurrence_time else '00:00',
    }

    return render(request, 'report_datapolicereport.html', context)
