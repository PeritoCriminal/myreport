from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.timezone import now
from django.urls import reverse
from myreportapp.models import ReportModel

@login_required
def report_requestauthority_view(request, report_id=None):
    current_user = request.user
    report = get_object_or_404(ReportModel, id=report_id)

    # Verifica se o relatório pertence ao usuário logado
    if report.user != current_user:
        raise Http404("Você não tem permissão para acessar este relatório.")

    if request.method == 'POST':
        section_request = request.POST.get('section_request', '').strip()
        requesting_authority = request.POST.get('requesting_authority', '').strip()
        examination_objective = request.POST.get('examination_objective', '').strip()
        call_date = request.POST.get('call_date', now().date())
        call_time = request.POST.get('call_time', '00:00:00')

        # Validações básicas antes de salvar
        if not requesting_authority or not examination_objective:
            context = {
                'error': "Todos os campos obrigatórios devem ser preenchidos.",
                'report': report
            }
            return render(request, 'report_datarequest.html', context)

        # Atualiza os dados do relatório
        report.has_authority_request = True
        report.section_request = section_request
        report.requesting_authority = requesting_authority
        report.examination_objective = examination_objective
        report.call_date = call_date
        report.call_time = call_time
        report.save()
        return redirect(reverse('report_showreport', kwargs={'report_id': report.id}))

    # Contexto para renderização inicial da página
    context = {
        'report_id': report.id,
        'section_request': report.section_request,
        'requesting_authority': report.requesting_authority if report else '',
        'examination_objective': report.examination_objective if report else '',
        'call_date': report.call_date.isoformat() if report and report.call_date else now().date().isoformat(),
        'call_time': report.call_time.strftime('%H:%M') if report and report.call_time else '00:00',
    }

    return render(request, 'report_datarequest.html', context)
