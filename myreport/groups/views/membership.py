from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from ..models import Group
from ..services import join_group, leave_group


@require_POST
@login_required
def group_join_view(request, pk):
    group = get_object_or_404(Group, pk=pk)
    try:
        join_group(group=group, user=request.user)
    except PermissionDenied:
        raise Http404("Grupo não encontrado.")
    return redirect("groups:group_detail", pk=group.pk)


@require_POST
@login_required
def group_leave_view(request, pk):
    group = get_object_or_404(Group, pk=pk)
    leave_group(group=group, user=request.user)
    return redirect("groups:group_detail", pk=group.pk)
