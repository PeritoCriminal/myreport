# path: myreport/report_maker/views/help_markdown.py

from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from report_maker.templatetags.markdown_extras import render_markdown


class MarkdownHelpView(TemplateView):
    template_name = "report_maker/help_markdown.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["examples"] = [
            {
                "title": "Negrito",
                "note": "A palavra em negrito entre duplos asteriscos.",
                "markdown": """Essa frase contem uma palavra em **negrito**

**Essa frase está em negrito**""",
            },
            {
                "title": "Itálico",
                "note": "Itálico entre asterisco simples.",
                "markdown": """Essa frase contem uma palavra em *itálico*

*Essa frase está em itálico*""",
            },
            {
                "title": "Combinar negrito e itálico",
                "markdown": """Essa frase contem um trecho em ***negrito e itálico***

***Essa frase está em negrito e itálico***""",
            },
            {
                "title": "Listas com marcadores",
                "markdown": """Abaixo temos uma lista com marcadores:

- Primeira linha
- Segunda linha
- Terceira linha""",
            },
            {
                "title": "Listas numeradas",
                "markdown": """Abaixo temos uma lista numerada:

1. Primeira linha
2. Segunda linha
3. Terceira linha""",
            },
            {
                "title": "Lista combinando estilos",
                "markdown": """A lista abaixo mostra os vestígios:

- **Vestígio 1**: Descrição do vestígio 1
- **Vestígio 2**: Descrição do vestígio 2""",
            },
            {
                "title": "Subtítulo",
                "markdown": """Esse é um parágrafo comum.

## Subtítulo

Esse é um novo parágrafo.""",
            },
            {
                "title": "Fórmulas matemáticas",
                "markdown": """Exemplos:

{math$ x^2 = y $}

{math$ x = \\sqrt{y} $}

{math$ \\frac{a}{b} $}

{math$ x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} $}""",
            },
        ]

        return context


@require_POST
def markdown_preview_view(request):
    """
    Renderiza markdown para preview usando o mesmo pipeline do sistema.
    """
    text = request.POST.get("text", "")
    return HttpResponse(render_markdown(text))