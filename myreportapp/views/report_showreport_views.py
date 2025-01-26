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
        
        preamble = (
            f'Em {report.designation_date}, na cidade de {current_user.city} e no Instituto de' 
            f'Criminalística da Superintendência da Polícia Técnico-Científica, '
            f'da Secretaria de Segurança Pública do Estado de São Paulo, '
            f'em conformidade com o disposto no art. 178 do Decreto-Lei 3689, '
            f'de 3 de outubro de 1941, e no Decreto-Lei 42847, de 9 de fevereiro de 1998, '
            f'pelo Diretor deste Instituto de Criminalística, '
            f'o Perito Criminal {report.institute_director}, '
            f'foi designado o perito criminal {report.expert_display_name} para proceder ao exame pericial' 
            f'especificado em requisição assinada pela Autoridade Policial, '
            f'o Delegado de Polícia {report.requesting_authority}.'
        )


    context = {
        'report_number': report.report_number,
        'preamble': preamble,
        'has_police_report': report.has_police_report,
        'has_authority_request': report.has_authority_request,
    }
    
    return render(request, 'report_showreport.html', context)