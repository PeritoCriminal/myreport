# report_maker/views/exam_objects_reorder.py
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from report_maker.models import GenericExamObject, PublicRoadExamObject  # ajuste

MODEL_MAP = {
    "GENERIC": GenericExamObject,
    "PUBLIC_ROAD": PublicRoadExamObject,
}

@login_required
@require_POST
def exam_objects_reorder(request):
    payload = json.loads(request.body.decode("utf-8"))
    report_id = payload["report_id"]
    items = payload["items"]  # [{id,type,order}, ...] (order vindo do JS pode ser ignorado)

    with transaction.atomic():
        for idx, it in enumerate(items, start=1):
            model = MODEL_MAP.get(it["type"])
            if not model:
                continue
            model.objects.filter(
                pk=it["id"],
                report_case_id=report_id,
            ).update(order=idx)

    return JsonResponse({"ok": True})
