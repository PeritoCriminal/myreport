from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from myreportapp.models import ReportModel, PreservationModel
from django.urls import reverse

@login_required
def report_preservation_view(request, report_id=None, preservation_id=None):
    
    # Verificar se o ID do report foi fornecido
    if not report_id:
        raise Http404("Relatório não encontrado.")

    # Buscar o ReportModel pelo ID e verificar se pertence ao usuário logado
    report = get_object_or_404(ReportModel, id=report_id, user=request.user)

    # Buscar PreservationModel, se o preservation_id for fornecido
    if preservation_id:
        preservation = get_object_or_404(PreservationModel, id=preservation_id, report=report)
    else:
        preservation = None

    # Se for um POST, salvar os dados enviados pelo formulário
    if request.method == "POST":
        # Coletar os dados enviados no formulário
        preservation_team = request.POST.get("preservation_team")
        officer_in_charge = request.POST.get("officer_in_charge")
        official_vehicle = request.POST.get("official_vehicle")
        police_authority_present = request.POST.get("police_authority_present") == "true"
        investigation_team_present = request.POST.get("investigation_team_present") == "true"
        general_context = request.POST.get("general_context")

        if preservation:
            # Atualizar PreservationModel existente
            preservation.preservation_team = preservation_team
            preservation.officer_in_charge = officer_in_charge
            preservation.official_vehicle = official_vehicle
            preservation.police_authority_present = police_authority_present
            preservation.investigation_team_present = investigation_team_present
            preservation.general_context = general_context
            preservation.save()
        else:
            # Criar um novo PreservationModel
            PreservationModel.objects.create(
                report=report,
                preservation_team=preservation_team,
                officer_in_charge=officer_in_charge,
                official_vehicle=official_vehicle,
                police_authority_present=police_authority_present,
                investigation_team_present=investigation_team_present,
                general_context=general_context,
            )

        # Redirecionar para a página do relatório
        return redirect(reverse("report_showreport", kwargs={"report_id": report.id}))

    # Contexto para renderizar o template
    context = {
        "report_id": report.id,
        "preservation": preservation,
        "preservation_team": preservation.preservation_team if preservation else "",
        "officer_in_charge": preservation.officer_in_charge if preservation else "",
        "official_vehicle": preservation.official_vehicle if preservation else "",
        "police_authority_present": preservation.police_authority_present if preservation else "",
        "investigation_team_present": preservation.investigation_team_present if preservation else "",
        "general_context": preservation.general_context if preservation else "",
    }

    return render(request, 'report_preservation.html', context)
