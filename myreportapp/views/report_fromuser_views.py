from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils.timezone import now
from django.urls import reverse
from myreportapp.models import ReportModel

@login_required
def report_fromuser_view(request, report_id=None):
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

        if report:
            report.expert_display_name = expert_display_name
            report.institute_director = institute_director
            report.institute_unit = institute_unit
            report.forensic_team_base = forensic_team_base
            report.save()
        else:
            report = ReportModel.objects.create(
                user=current_user,
                expert_display_name=current_user.display_name,
                institute_director=institute_director,
                institute_unit=institute_unit,
                forensic_team_base=forensic_team_base,
            )


        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'message': 'Relatório salvo com sucesso!',
                'report_id': report.id,
            })
        else:
            return redirect(reverse('report_showreport', kwargs={'report_id': report.id}))


    context = {
    'report_id': report.id,
    'expert_display_name': report.expert_display_name if report else current_user.display_name,
    'institute_director': report.institute_director if report else current_user.director,
    'institute_unit': report.institute_unit if report else current_user.unit,
    'forensic_team_base': report.forensic_team_base if report else current_user.team,
    }

    return render(request, 'report_datafromuser.html', context)
