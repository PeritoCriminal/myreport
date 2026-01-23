# report_maker/views/exam_objects_reorder.py
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from report_maker.models import ExamObject, ReportCase


@login_required
@require_POST
def exam_objects_reorder(request):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    report_id = payload.get("report_id")
    items = payload.get("items") or []  # [{id,type,order}, ...]

    report = get_object_or_404(ReportCase.objects.select_related("author"), pk=report_id)
    if report.author_id != request.user.id:
        raise PermissionDenied("Acesso negado.")
    if not report.can_edit:
        raise PermissionDenied("Este laudo está bloqueado para edição.")

    ids = [it.get("id") for it in items if it.get("id")]
    if not ids:
        return JsonResponse({"ok": False, "error": "Lista vazia."}, status=400)

    # garante que todos os ids pertencem ao laudo
    found = set(
        ExamObject.objects
        .filter(report_case=report, pk__in=ids)
        .values_list("pk", flat=True)
    )
    missing = [i for i in ids if i not in {str(x) for x in found}]
    if missing:
        return JsonResponse({"ok": False, "error": "IDs não pertencem ao laudo.", "missing": missing}, status=400)

    # atualização em duas etapas para não violar uq(report_case, order)
    with transaction.atomic():
        # 1) desloca para uma faixa alta temporária
        bump = 10_000
        for idx, obj_id in enumerate(ids, start=1):
            ExamObject.objects.filter(report_case=report, pk=obj_id).update(order=bump + idx)

        # 2) aplica a ordem final
        for idx, obj_id in enumerate(ids, start=1):
            ExamObject.objects.filter(report_case=report, pk=obj_id).update(order=idx)

    return JsonResponse({"ok": True})
