from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction

from .models import Group, GroupMembership


def join_group(*, group: Group, user) -> bool:
    """
    Retorna True se entrou; False se já era membro.
    """
    if not group.is_active:
        raise PermissionDenied("Grupo inativo.")

    try:
        with transaction.atomic():
            GroupMembership.objects.create(group=group, user=user)
        return True
    except IntegrityError:
        return False


def leave_group(*, group: Group, user) -> int:
    """
    Remove a membership. Retorna quantidade removida (0 ou 1).
    """
    return GroupMembership.objects.filter(group=group, user=user).delete()[0]


def inactivate_group(*, group: Group, user) -> None:
    """
    Apenas o criador pode inativar.
    """
    if group.creator_id != user.id:
        raise PermissionDenied("Apenas o criador do grupo pode inativar.")

    if group.is_active:
        group.is_active = False
        group.save(update_fields=["is_active"])
