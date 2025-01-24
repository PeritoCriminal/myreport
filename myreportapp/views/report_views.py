from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils.timezone import now
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
        expert_display_name = request.POST.get('expert_display_name', '').strip()
        institute_director = request.POST.get('institute_director', '').strip()
        institute_unit = request.POST.get('institute_unit', '').strip()
        forensic_team_base = request.POST.get('forensic_team_base', '').strip()
        report_number = request.POST.get('report_number', '').strip()
        protocol_number = request.POST.get('protocol_number', '').strip()
        designation_date = request.POST.get('designation_date', now().date())
        service_date = request.POST.get('service_date', now().date())
        service_time = request.POST.get('service_time', '00:00:00')
        photographer = request.POST.get('photographer', '').strip()
        considerations = request.POST.get('considerations', '').strip()
        conclusion = request.POST.get('conclusion', '').strip()

        if report:
            report.expert_display_name = expert_display_name
            report.institute_director = institute_director
            report.institute_unit = institute_unit
            report.forensic_team_base = forensic_team_base
            report.report_number = report_number
            report.protocol_number = protocol_number
            report.designation_date = designation_date
            report.service_date = service_date
            report.service_time = service_time
            report.photographer = photographer
            report.considerations = considerations
            report.conclusion = conclusion
            report.save()
        else:
            report = ReportModel.objects.create(
                user=current_user,
                expert_display_name=current_user.display_name,
                institute_director=institute_director,
                institute_unit=institute_unit,
                forensic_team_base=forensic_team_base,
                report_number=report_number,
                protocol_number=protocol_number,
                designation_date=designation_date,
                service_date=service_date,
                service_time=service_time,
                photographer=photographer,
                considerations=considerations,
                conclusion=conclusion,
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'message': 'Relatório salvo com sucesso!',
                'report_id': report.id,
            })
        else:
            return redirect('home')

    context = {
    'expert_display_name': report.expert_display_name if report else current_user.display_name,
    'institute_director': report.institute_director if report else current_user.director,
    'institute_unit': report.institute_unit if report else current_user.unit,
    'forensic_team_base': report.forensic_team_base if report else current_user.team,
    'report_photographer': report.photographer if report else '',
    'report_number': report.report_number if report else '',
    'protocol_number': report.protocol_number if report else '',
    'designation_date': report.designation_date.isoformat() if report and report.designation_date else now().date().isoformat(),
    'service_date': report.service_date.isoformat() if report and report.service_date else now().date().isoformat(),
    'service_time': report.service_time.isoformat() if report and report.service_time else '00:00',
    'considerations': report.considerations if report else '',
    'conclusion': report.conclusion if report else '',
    }

    return render(request, 'report_dataheader.html', context)
