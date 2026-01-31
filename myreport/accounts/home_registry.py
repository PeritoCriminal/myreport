from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from django.urls import NoReverseMatch, reverse, reverse_lazy


@dataclass(frozen=True)
class HomeItem:
    key: str
    label: str
    url_name: str
    allowed: Callable  # allowed(user) -> bool


def allowed_dashboard(user) -> bool:
    return bool(user and user.is_authenticated)


def allowed_posts(user) -> bool:
    return bool(user and user.is_authenticated)


def allowed_groups(user) -> bool:
    return bool(user and user.is_authenticated)


def allowed_technical(user) -> bool:
    return bool(user and user.is_authenticated)


def allowed_reports(user) -> bool:
    return bool(user and user.is_authenticated)


def allowed_zen(user) -> bool:
    return bool(user and user.is_authenticated)


HOME_ITEMS: list[HomeItem] = [
    HomeItem("dashboard", "Dashboard", "home:dashboard", allowed_dashboard),
    HomeItem("posts", "Postagens", "social_net:post_list", allowed_posts),
    HomeItem("groups", "Grupos", "groups:group_list", allowed_groups),
    HomeItem("technical", "Arquivo técnico", "technical_repository:document_list", allowed_technical),
    HomeItem("reports", "Laudos", "report_maker:reportcase_list", allowed_reports),
    HomeItem("zen", "Zen do Laudo", "home:zen_do_laudo", allowed_zen),
]


def get_home_keys() -> set[str]:
    return {i.key for i in HOME_ITEMS}


def _url_name_exists(url_name: str) -> bool:
    try:
        reverse(url_name)
        return True
    except NoReverseMatch:
        return False


def get_allowed_home_choices(user):
    return [(i.key, i.label) for i in HOME_ITEMS if i.allowed(user)]


def get_home_url_for_user(user, key: str) -> str | None:
    for i in HOME_ITEMS:
        if i.key == key and i.allowed(user):
            try:
                return str(reverse_lazy(i.url_name))
            except NoReverseMatch:
                return None
    return None


def get_fallback_home_url(user) -> str:
    for i in HOME_ITEMS:
        if i.allowed(user):
            try:
                return str(reverse_lazy(i.url_name))
            except NoReverseMatch:
                continue
    return str(reverse_lazy("home:dashboard"))
