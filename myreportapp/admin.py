from django.contrib import admin
from myreportapp.models import ReportModel,PreservationModel

@admin.register(ReportModel)
class ReportModelAdmin(admin.ModelAdmin):    
    list_display = (
        'report_number', 
        'protocol_number', 
        'report_date', 
        'updated_at', 
        'expert_display_name', 
        'service_date', 
        'city'
    )
    list_filter = ('service_date', 'city', 'incident_nature')  # Filtros laterais úteis
    search_fields = ('report_number', 'protocol_number', 'city', 'incident_nature', 'has_police_report')  # Barra de pesquisa
    ordering = ('-report_date',)  # Ordena do mais recente para o mais antigo
    readonly_fields = ('updated_at', 'report_date')  # Campos somente leitura

@admin.register(PreservationModel)
class PreservationModelAdmin(admin.ModelAdmin):
    list_display = (
        'report',
        'general_context'
    )

    



