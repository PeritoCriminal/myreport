from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils.timezone import now
from myreportapp.models import ReportModel, PreservationModel
from commonapp.commondefs import fulldate

@login_required
def report_showreport_view(request, report_id=None):
    current_user = request.user
    report = None

    if report_id:
        report = get_object_or_404(ReportModel, id=report_id)
        if report.user != current_user:
            raise Http404("Você não tem permissão para acessar este relatório.")
        
        expert_gender = 'Perito(a) Responsável'
        if current_user.gender == 'M':
            expert_gender = 'Perito Responsável'
        elif current_user.gender == 'F':
            expert_gender = 'Perita Responsável'
        else:
            expert_gender = 'Perito(a) Responsável'
        
    def makepreamble():
        # Obtenção da data por extenso
        datedesignation = fulldate(report.designation_date)
        city = current_user.city

        # Montagem do texto do diretor ou diretora
        if 'Dra.' in report.institute_director:
            director = f'pela Diretora deste Instituto de Criminalística, Perita Criminal {report.institute_director}'
        elif 'Dr.' in report.institute_director:
            director = f'pelo Diretor deste Instituto de Criminalística, Perito Criminal {report.institute_director}'
        else:
            director = f'pelo(a) Diretor(a) deste Instituto de Criminalística, Perito(a) Criminal {report.institute_director}'

        # Montagem do texto do perito ou perita
        if current_user.gender == 'M':
            expertdisplayname = f'designado o Perito Criminal {report.expert_display_name}'
        elif current_user.gender == 'F':
            expertdisplayname = f'designada a Perita Criminal {report.expert_display_name}'
        else:
            expertdisplayname = f'designado(a) o(a) Perito(a) Criminal {report.expert_display_name}'

        # Montagem do texto da autoridade requisitante
        if 'Dra.' in report.requesting_authority:
            authority = f'a Delegada de Polícia {report.requesting_authority}'
        elif 'Dr.' in report.requesting_authority:
            authority = f'o Delegado de Polícia {report.requesting_authority}'
        else:
            authority = f'o(a) Delegado(a) de Polícia {report.requesting_authority}'

        # Construção do preâmbulo
        return (
            f"Em {datedesignation}, na cidade de {city}, no Instituto de "
            f"Criminalística da Superintendência da Polícia Técnico-Científica, "
            f"da Secretaria de Segurança Pública do Estado de São Paulo, "
            f"em conformidade com o disposto no art. 178 do Decreto-Lei nº 3.689 "
            f"de 3 de outubro de 1941, "
            f"{director}, "
            f"foi {expertdisplayname} para proceder ao exame pericial "
            f"especificado na Requisição expedida pela Autoridade Policial, "
            f"{authority}."
        )    
    

    preamble = makepreamble()

    preservations = PreservationModel.objects.filter(report__id=report_id) 

    context = {
        'preservations': preservations,
        'report_id': report.id,
        'report_number': report.report_number,
        'expert_display_name': report.expert_display_name,
        'expert_gender': expert_gender,
        'protocol_number': report.protocol_number,
        'service_date': report.service_date,
        'service_time': report.service_time,
        'photographer': report.photographer,
        'preamble': preamble,
        'has_police_report': report.has_police_report,
        'police_report_number': report.police_report_number,
        'police_station': report.police_station,
        'occurrence_date': report.occurrence_date,
        'occurrence_time': report.occurrence_time,
        'incident_nature': report.incident_nature,
        'has_authority_request': report.has_authority_request,
        'authority': report.requesting_authority,
        'objective': report.examination_objective,
        'call_date': report.call_date,
        'call_time': report.call_time,
    }
    
    return render(request, 'report_showreport.html', context)