from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils.timezone import now
from django.urls import reverse
from myreportapp.models import ReportModel

@login_required
def report_dataheader_view(request, report_id=None):
    current_user = request.user
    report = None

    if report_id:
        report = get_object_or_404(ReportModel, id=report_id)
        if report.user != current_user:
            raise Http404("Você não tem permissão para acessar este relatório.")

    if request.method == 'POST':
        report_number = request.POST.get('report_number', '').strip()
        protocol_number = request.POST.get('protocol_number', '').strip()
        designation_date = request.POST.get('designation_date', now().date())
        service_date = request.POST.get('service_date', now().date())
        service_time = request.POST.get('service_time', '00:00:00')
        photographer = request.POST.get('photographer', '').strip()

        if report:
            report.report_number = report_number
            report.protocol_number = protocol_number
            report.designation_date = designation_date
            report.service_date = service_date
            report.service_time = service_time
            report.photographer = photographer
            report.save()
        else:
            report = ReportModel.objects.create(
                user=current_user,
                expert_display_name=current_user.display_name,
                report_number=report_number,
                protocol_number=protocol_number,
                designation_date=designation_date,
                service_date=service_date,
                service_time=service_time,
                photographer=photographer,
            )


        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'message': 'Relatório salvo com sucesso!',
                'report_id': report.id,
            })
        else:
            return redirect(reverse('report_showreport', kwargs={'report_id': report.id}))


    context = {
    'report_photographer': report.photographer if report else '',
    'report_number': report.report_number if report else '',
    'protocol_number': report.protocol_number if report else '',
    'designation_date': report.designation_date.isoformat() if report and report.designation_date else now().date().isoformat(),
    'service_date': report.service_date.isoformat() if report and report.service_date else now().date().isoformat(),
    'service_time': report.service_time.isoformat() if report and report.service_time else '00:00',
    }

    return render(request, 'report_dataheader.html', context)
