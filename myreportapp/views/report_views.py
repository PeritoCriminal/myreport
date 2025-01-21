from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now
from myreportapp.models import ReportModel  # Certifique-se de importar o modelo correto

@login_required
def report_dataheader_view(request):
    if request.method == 'POST':
        # Obtenha os dados enviados via POST
        report_number = request.POST.get('report_number', '').strip()
        protocol_number = request.POST.get('protocol_number', '').strip()
        designation_date = request.POST.get('designation_date', now().date())
        service_date = request.POST.get('service_date', now().date())
        service_time = request.POST.get('service_time', '00:00:00')
        photographer = request.POST.get('photographer', '').strip()
        considerations = request.POST.get('considerations', '').strip()
        conclusion = request.POST.get('conclusion', '').strip()

        # Salve os dados no banco de dados
        report = ReportModel.objects.create(
            report_number=report_number,
            protocol_number=protocol_number,
            designation_date=designation_date,
            service_date=service_date,
            service_time=service_time,
            photographer=photographer,
            considerations=considerations,
            conclusion=conclusion,
        )

        # Verifique o tipo de resposta: JSON ou redirecionamento
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Verifica se é uma requisição AJAX
            return JsonResponse({
                'message': 'Relatório salvo com sucesso!',
                'report_id': report.id,
            })
        else:
            # Redirecione para uma página de sucesso ou exibição de relatórios
            return redirect('home')  # Certifique-se de configurar a URL correspondente

    # Para requisições GET, renderize o formulário
    return render(request, 'report_dataheader.html')
