from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from myreportapp.models import ReportModel  # Substitua pelo modelo correto do seu relatório

@login_required
def report_userreportlist_view(request):
    # Obter os relatórios pertencentes ao usuário logado
    user_reports = ReportModel.objects.filter(user=request.user)
    
    # Renderizar o template com os relatórios do usuário
    return render(request, 'report_userreportlist.html', {'reports': user_reports})
