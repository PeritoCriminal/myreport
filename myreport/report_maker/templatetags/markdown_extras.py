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


register = template.Library()

# Tags permitidas para o conteúdo textual
_ALLOWED_TAGS = [
    "p", "br",
    "strong", "em", "s", "code", "pre",
    "blockquote",
    "ul", "ol", "li",
    "h1", "h2", "h3",
    "hr",
    "span",
]

# Tags específicas do KaTeX/MathML para garantir que subscritos e sobrescritos funcionem
_MATH_TAGS = [
    "math", "semantics", "mrow", "mi", "mn", "mo", "mtext", 
    "annotation", "msub", "msup", "mover", "munder", 
    "msubsup", "mtable", "mtr", "mtd", "mspace"
]

_ALLOWED_TAGS.extend(_MATH_TAGS)

# Atributos permitidos (essencial permitir 'style' em spans para o layout do KaTeX)
_ALLOWED_ATTRS = {
    "code": ["class"],
    "pre": ["class"],
    "span": ["class", "aria-hidden", "style", "dir"],
    "math": ["xmlns", "display"],
    "annotation": ["encoding"],
}

_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

# Detecta expressões matemáticas inline: $...$
_INLINE_MATH_RE = re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$", re.DOTALL)


def _render_katex_inline(tex: str) -> str:
    """
    Renderiza expressão TeX inline usando a CLI do KaTeX.
    """
    try:
        result = subprocess.run(
            [str(settings.KATEX_CLI_BIN), "--no-throw-on-error"],
            input=tex,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()

    except Exception:
        # fallback seguro caso KaTeX falhe ou binário não encontrado
        escaped = html.escape(tex)
        return f'<span class="math-inline-error">${escaped}$</span>'


@register.filter
def render_markdown(value: str) -> str:
    """
    Converte Markdown para HTML, isolando fórmulas matemáticas para evitar
    conflitos de caracteres como '_' e '^', e sanitiza o resultado.
    """
    text = (value or "").strip()
    if not text:
        return ""

    # 1. MASCARAR: Extrair fórmulas e substituir por placeholders
    # Isso evita que o Markdown tente converter x_2 em itálico.
    math_map = {}
    def mask_math(match):
        placeholder = f"MATH-PH-{uuid.uuid4()}"
        tex = match.group(1).strip()
        # Renderiza via CLI e armazena o HTML resultante
        math_map[placeholder] = _render_katex_inline(tex)
        return placeholder

    text_masked = _INLINE_MATH_RE.sub(mask_math, text)

    # 2. MARKDOWN: Converter o texto que agora contém apenas os placeholders
    html_out = md.markdown(
        text_masked,
        extensions=[
            "fenced_code",
            "sane_lists",
            "nl2br",
        ],
        output_format="html5",
    )

    # 3. REINSERIR: Substituir os placeholders pelo HTML renderizado do KaTeX
    for placeholder, rendered_math in math_map.items():
        html_out = html_out.replace(placeholder, rendered_math)

    # 4. SANITIZAR: Limpar o HTML mantendo as tags necessárias para a matemática
    clean = bleach.clean(
        html_out,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )

    return mark_safe(clean)