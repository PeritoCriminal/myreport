# path: myreport/report_maker/templatetags/markdown_extras.py

import html
import re
import subprocess
import uuid

import markdown as md
import bleach

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from bleach.css_sanitizer import CSSSanitizer


register = template.Library()


# Propriedades CSS necessárias para preservar o layout gerado pelo KaTeX
_ALLOWED_CSS_PROPERTIES = [
    "display", "height", "width", "top", "bottom", "vertical-align",
    "margin-top", "margin-left", "margin-right", "margin-bottom",
    "position", "border-color", "float", "color", "background-color",
]


# Conjunto de tags HTML permitidas após sanitização
_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "s", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "hr", "span",
    # MathML utilizado pelo KaTeX
    "math", "semantics", "mrow", "mi", "mn", "mo", "mtext",
    "annotation", "msub", "msup", "mover", "munder",
    "msubsup", "mtable", "mtr", "mtd", "mspace", "menclose",
]


# Atributos necessários para preservar classes e estilos de layout do KaTeX
_ALLOWED_ATTRS = {
    "*": ["class", "style", "id"],
    "span": ["aria-hidden", "dir"],
    "math": ["xmlns", "display"],
    "annotation": ["encoding"],
    "code": ["class"],
}


_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


# Sanitizador CSS utilizado pelo bleach
_CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=_ALLOWED_CSS_PROPERTIES
)


# Regex aprimorado para capturar fórmulas mesmo sem espaços, mas ignorando moedas escapadas
_INLINE_MATH_RE = re.compile(r"(?<!\\)\$([^\$]+?)(?<!\\)\$")


def _render_katex_inline(tex: str) -> str:
    """Renderiza expressão TeX inline utilizando a CLI do KaTeX."""
    try:
        result = subprocess.run(
            [str(settings.KATEX_CLI_BIN), "--no-throw-on-error"],
            input=tex,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except Exception:
        return f'<span class="math-error">${html.escape(tex)}$</span>'


@register.filter
def render_markdown(value: str) -> str:
    """
    Converte Markdown para HTML protegendo moedas e renderizando KaTeX.
    """
    text = (value or "").strip()
    if not text:
        return ""

    # 1. Proteção de Moedas: Escapa R$, U$ e $ seguido de número
    # O regex r'(\b[RU]\$|\$\s?\d)' protege "R$", "U$" e "$ 10" ou "$10"
    text = re.sub(r'(\b[RU]\$|\$\s?\d)', lambda m: m.group(0).replace('$', r'\$'), text)

    math_map = {}

    def mask_math(match):
        placeholder = f"KATEXPH{uuid.uuid4().hex}"
        tex_content = match.group(1).strip()
        # Restaura cifrões internos se o usuário escapou manualmente na fórmula
        tex_content = tex_content.replace(r'\$', '$')
        math_map[placeholder] = _render_katex_inline(tex_content)
        return placeholder

    # 2. Aplica o Regex de Matemática
    text_masked = _INLINE_MATH_RE.sub(mask_math, text)

    # 3. Conversão Markdown
    html_out = md.markdown(
        text_masked,
        extensions=["fenced_code", "sane_lists", "nl2br"],
        output_format="html5",
    )

    # 4. Reinsere KaTeX
    for placeholder, rendered_math in math_map.items():
        html_out = html_out.replace(placeholder, rendered_math)

    # 5. Sanitização
    clean = bleach.clean(
        html_out,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        css_sanitizer=_CSS_SANITIZER,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )

    # 6. Restauração Final: Remove escapes de moeda para exibição limpa
    clean = clean.replace(r'\$', '$')

    return mark_safe(clean)