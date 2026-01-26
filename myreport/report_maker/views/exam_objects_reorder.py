# report_maker/views/exam_objects_reorder.py
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from report_maker.models import ExamObject, ReportCase


@login_required
@require_POST
def exam_objects_reorder(request, pk):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    items = payload.get("items") or []  # [{id,type,order}, ...]

    report = get_object_or_404(
        ReportCase.objects.select_related("author"),
        pk=pk,
    )

    if report.author_id != request.user.id:
        raise PermissionDenied("Acesso negado.")
    if not report.can_edit:
        raise PermissionDenied("Este laudo está bloqueado para edição.")

    raw_ids = [it.get("id") for it in items if it.get("id")]
    if not raw_ids:
        return JsonResponse({"ok": False, "error": "Lista vazia."}, status=400)

    # normaliza para string e remove duplicados mantendo a ordem
    ids: list[str] = []
    seen: set[str] = set()
    for _id in raw_ids:
        s = str(_id)
        if s not in seen:
            seen.add(s)
            ids.append(s)

    found = set(
        ExamObject.objects.filter(report_case=report, pk__in=ids)
        .values_list("pk", flat=True)
    )
    found_str = {str(x) for x in found}

    missing = [i for i in ids if i not in found_str]
    if missing:
        return JsonResponse(
            {"ok": False, "error": "IDs não pertencem ao laudo.", "missing": missing},
            status=400,
        )

    bump = 10_000

    # 2 updates totais (com CASE), mantendo a técnica do "bump"
    bump_cases = [When(pk=obj_id, then=Value(bump + idx)) for idx, obj_id in enumerate(ids, start=1)]
    final_cases = [When(pk=obj_id, then=Value(idx)) for idx, obj_id in enumerate(ids, start=1)]

    with transaction.atomic():
        ExamObject.objects.filter(report_case=report, pk__in=ids).update(
            order=Case(*bump_cases, default=Value(bump), output_field=IntegerField())
        )
        ExamObject.objects.filter(report_case=report, pk__in=ids).update(
            order=Case(*final_cases, default=Value(0), output_field=IntegerField())
        )

    return JsonResponse({"ok": True})
