from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver

EXCLUDE_PREFIXES = (
    "admin/",
    "media/",
    "static/",
    "^media/",
    "^static/",
    "^admin/",
)


class Command(BaseCommand):
    help = "Lista rotas do projeto (excluindo admin e media/static)"

    def handle(self, *args, **options):
        resolver = get_resolver()
        self.print_urls(resolver.url_patterns)

    def _callback_label(self, callback):
        # CBV (as_view) -> tenta extrair a classe real
        view_cls = getattr(callback, "view_class", None)
        if view_cls:
            return f"{view_cls.__module__}.{view_cls.__name__}"
        return f"{callback.__module__}.{callback.__name__}"

    def print_urls(self, patterns, prefix=""):
        for p in patterns:
            if isinstance(p, URLPattern):
                full_path = f"{prefix}{p.pattern}"

                if full_path.startswith(EXCLUDE_PREFIXES):
                    continue

                route_name = p.name or "-"
                label = self._callback_label(p.callback)

                self.stdout.write(
                    f"{full_path:<45} {label:<55} {route_name}"
                )

            elif isinstance(p, URLResolver):
                self.print_urls(
                    p.url_patterns,
                    prefix=f"{prefix}{p.pattern}",
                )
