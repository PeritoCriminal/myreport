import markdown as md
import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ALLOWED_TAGS = [
    "p", "br",
    "strong", "em", "s", "code", "pre",
    "blockquote",
    "ul", "ol", "li",
    "h1", "h2", "h3",
    "hr",
]

_ALLOWED_ATTRS = {
    # se futuramente você quiser links:
    # "a": ["href", "title", "rel", "target"],
    "code": ["class"],
    "pre": ["class"],
}

_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


@register.filter
def render_markdown(value: str) -> str:
    """
    Converte Markdown para HTML e sanitiza (XSS-safe).
    """
    text = (value or "").strip()
    if not text:
        return ""

    html = md.markdown(
        text,
        extensions=[
            "fenced_code",
            "sane_lists",
        ],
        output_format="html5",
    )

    clean = bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )

    return mark_safe(clean)
