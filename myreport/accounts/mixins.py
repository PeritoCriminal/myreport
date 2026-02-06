# accounts/mixins.py
from __future__ import annotations

from django.core.exceptions import PermissionDenied


class CanCreateReportsRequiredMixin:
    """
    Exige permissão efetiva para CRIAR novos laudos.

    Regra aplicada:
    - usuário autenticado;
    - user.can_create_reports_effective == True.

    A lógica de autorização é centralizada no model User.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.can_create_reports_effective:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class CanEditReportsRequiredMixin:
    """
    Exige permissão efetiva para EDITAR laudos já existentes.

    Regra aplicada:
    - usuário autenticado;
    - user.can_edit_reports_effective == True.

    A lógica de autorização é centralizada no model User.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.can_edit_reports_effective:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
