# path: myreport/report_maker/templatetags/markdown_extras.py

from __future__ import annotations

import html
import re
import subprocess
import uuid

import bleach
import markdown as md
from bleach.css_sanitizer import CSSSanitizer
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


register = template.Library()


_ALLOWED_CSS_PROPERTIES = [
    "background-color",
    "border-color",
    "bottom",
    "color",
    "display",
    "float",
    "height",
    "margin-bottom",
    "margin-left",
    "margin-right",
    "margin-top",
    "position",
    "top",
    "vertical-align",
    "width",
]

_ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "s",
    "code",
    "pre",
    "blockquote",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "hr",
    "span",
    # MathML utilizado pelo KaTeX
    "math",
    "semantics",
    "mrow",
    "mi",
    "mn",
    "mo",
    "mtext",
    "annotation",
    "msub",
    "msup",
    "mover",
    "munder",
    "msubsup",
    "mtable",
    "mtr",
    "mtd",
    "mspace",
    "menclose",
    # SVG utilizado pelo KaTeX em alguns símbolos e raízes
    "svg",
    "path",
    "line",
]

_ALLOWED_ATTRS = {
    "*": ["class", "style", "id"],
    "span": ["aria-hidden", "dir"],
    "math": ["xmlns", "display"],
    "annotation": ["encoding"],
    "code": ["class"],
    "svg": [
        "xmlns",
        "width",
        "height",
        "viewBox",
        "preserveAspectRatio",
        "role",
        "focusable",
        "aria-hidden",
        "style",
        "class",
    ],
    "path": [
        "d",
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-miterlimit",
        "transform",
        "style",
        "class",
    ],
    "line": [
        "x1",
        "x2",
        "y1",
        "y2",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "transform",
        "style",
        "class",
    ],
}

_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

_CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=_ALLOWED_CSS_PROPERTIES
)

_INLINE_MATH_RE = re.compile(
    r"\{math\$\s*(.*?)\s*\$\}",
    re.DOTALL,
)


def _render_katex_inline(tex: str) -> str:
    """
    Renderiza expressão TeX inline utilizando a CLI do KaTeX.
    """
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
        return f'<span class="math-error">{html.escape(tex)}</span>'


@register.filter
def render_markdown(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    math_map: dict[str, str] = {}

    # 1. Mascarar o conteúdo TeX para que o Markdown não o corrompa
    def mask_math(match: re.Match[str]) -> str:
        placeholder = f"KATEXPH{uuid.uuid4().hex}"
        # Guardamos apenas o texto TeX puro para renderizar DEPOIS da limpeza
        math_map[placeholder] = match.group(1).strip()
        return placeholder

    text_masked = _INLINE_MATH_RE.sub(mask_math, text)

    # 2. Converter Markdown para HTML
    html_out = md.markdown(
        text_masked,
        extensions=["fenced_code", "sane_lists", "nl2br"],
        output_format="html5",
    )

    # 3. Sanitizar o HTML produzido pelo Markdown (limpa tags maliciosas)
    # Aqui o Bleach não mexerá nos nossos placeholders KATEXPH...
    clean = bleach.clean(
        html_out,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        css_sanitizer=_CSS_SANITIZER,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )

    # 4. Agora sim, renderizar o KaTeX e substituir os placeholders
    # Como o KaTeX CLI gera um HTML complexo e confiável, inserimos após a limpeza
    for placeholder, tex_content in math_map.items():
        rendered_math = _render_katex_inline(tex_content)
        clean = clean.replace(placeholder, rendered_math)

    return mark_safe(clean)