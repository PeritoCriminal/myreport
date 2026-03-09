# path: myreport/report_maker/views/help_markdown.py

from django.views.generic import TemplateView

from common.mixins import BootstrapFormMixin


class MarkdownHelpView(TemplateView):
    """
    Exibe página de ajuda para uso do editor Markdown do sistema.
    """
    template_name = "report_maker/help_markdown.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ajuda do editor Markdown"
        return context
