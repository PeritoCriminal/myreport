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

    items = payload.get("items") or []  # [{id}, ...]
    raw_ids = [it.get("id") for it in items if it.get("id")]
    if not raw_ids:
        return JsonResponse({"ok": False, "error": "Lista vazia."}, status=400)

    report = get_object_or_404(
        ReportCase.objects.select_related("author"),
        pk=pk,
    )

    if report.author_id != request.user.id:
        raise PermissionDenied("Acesso negado.")
    if not report.can_edit:
        raise PermissionDenied("Este laudo está bloqueado para edição.")

    # normaliza para string e remove duplicados mantendo a ordem
    ids: list[str] = []
    seen: set[str] = set()
    for _id in raw_ids:
        s = str(_id)
        if s not in seen:
            seen.add(s)
            ids.append(s)

    # 1) Confere se todos IDs pertencem ao laudo e descobre o group_key real (inclui NULL)
    rows = list(
        ExamObject.objects.filter(report_case=report, pk__in=ids)
        .values_list("pk", "group_key")
    )
    found_str = {str(pk) for pk, _gk in rows}

    missing = [i for i in ids if i not in found_str]
    if missing:
        return JsonResponse(
            {"ok": False, "error": "IDs não pertencem ao laudo.", "missing": missing},
            status=400,
        )

    group_keys = {gk for _pk, gk in rows}  # pode conter None
    if len(group_keys) != 1:
        return JsonResponse(
            {
                "ok": False,
                "error": "IDs pertencem a grupos diferentes.",
                "group_keys": [str(x) if x is not None else None for x in group_keys],
            },
            status=400,
        )

    target_group_key = next(iter(group_keys))  # None OU string

    "target_group_key"

    # 2) Monta o estado atual global (ordem do laudo) e agrupa preservando a sequência dos grupos
    all_rows = list(
        ExamObject.objects.filter(report_case=report)
        .order_by("order", "created_at", "id")
        .values_list("pk", "group_key")
    )

    # Sequência de grupos conforme aparecem no laudo (primeira ocorrência)
    group_sequence: list[object] = []
    grouped: dict[object, list[str]] = {}

    for pk_val, gk in all_rows:
        if gk not in grouped:
            grouped[gk] = []
            group_sequence.append(gk)
        grouped[gk].append(str(pk_val))

    # 3) Valida: a lista enviada deve representar o grupo TODO (senão bagunça o restante do grupo)
    expected_ids = grouped.get(target_group_key, [])
    expected_set = set(expected_ids)

    if len(ids) != len(expected_set):
        return JsonResponse(
            {
                "ok": False,
                "error": "Lista incompleta para o grupo informado.",
                "group_key": target_group_key,
                "expected_count": len(expected_set),
                "received_count": len(ids),
            },
            status=400,
        )

    if set(ids) != expected_set:
        # ids contém itens de fora ou faltando itens do grupo
        return JsonResponse(
            {
                "ok": False,
                "error": "Lista inválida para o grupo informado.",
                "group_key": target_group_key,
            },
            status=400,
        )

    # 4) Aplica a nova ordem interna do grupo alvo (inclui NULL) e recalcula ordem GLOBAL 1..N
    grouped[target_group_key] = ids

    new_global_ids: list[str] = []
    for gk in group_sequence:
        new_global_ids.extend(grouped.get(gk, []))

    # Se por algum motivo algo ficou inconsistente
    if len(new_global_ids) != len(all_rows):
        return JsonResponse(
            {"ok": False, "error": "Falha ao reconstruir ordem global."},
            status=500,
        )

    # 5) Persiste com técnica do "bump" no LAUDO TODO (evita colisão do UniqueConstraint)
    bump = 10_000

    bump_cases = [
        When(pk=obj_id, then=Value(bump + idx))
        for idx, obj_id in enumerate(new_global_ids, start=1)
    ]
    final_cases = [
        When(pk=obj_id, then=Value(idx))
        for idx, obj_id in enumerate(new_global_ids, start=1)
    ]

    with transaction.atomic():
        ExamObject.objects.filter(report_case=report, pk__in=new_global_ids).update(
            order=Case(*bump_cases, default=Value(bump), output_field=IntegerField())
        )
        ExamObject.objects.filter(report_case=report, pk__in=new_global_ids).update(
            order=Case(*final_cases, default=Value(0), output_field=IntegerField())
        )

    return JsonResponse({"ok": True, "group_key": target_group_key})
