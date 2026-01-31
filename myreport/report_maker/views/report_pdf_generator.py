# report_maker/views/report_pdf_generator.py
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from weasyprint import HTML, CSS

from report_maker.models import ReportCase, ReportTextBlock
from report_maker.models.images import ObjectImage
from report_maker.views.report_outline import build_report_outline


@login_required
def reportPDFGenerator(request, pk):
    report = get_object_or_404(
        ReportCase.objects.select_related(
            "author",
            "institution",
            "nucleus",
            "team",
        ),
        pk=pk,
        author=request.user,
    )

    # ------------------------------------------------------------------
    # Textos do laudo (mesma regra do showpage)
    # ------------------------------------------------------------------
    text_blocks_qs = report.text_blocks.all().order_by(
        "placement", "position", "created_at"
    )

    # Preâmbulo: usuário > sistema
    preamble_text = (
        text_blocks_qs
        .filter(placement=ReportTextBlock.Placement.PREAMBLE)
        .values_list("body", flat=True)
        .first()
    )
    preamble = (preamble_text or "").strip() or report.preamble

    # ------------------------------------------------------------------
    # Objetos do exame
    # ------------------------------------------------------------------
    base_objects = list(
        report.exam_objects.all().order_by("order", "created_at")
    )
    concrete_objects = [o.concrete for o in base_objects]

    # ------------------------------------------------------------------
    # Outline (inclui Dados da Requisição / Atendimento / Objetivo)
    # ------------------------------------------------------------------
    outline, next_top = build_report_outline(
        report=report,
        exam_objects_qs=base_objects,
        text_blocks_qs=text_blocks_qs,
        start_at=1,
        prepend_blocks=report.get_render_blocks(),  # 🔴 MESMO pipeline
    )

    # ------------------------------------------------------------------
    # Conclusão (último T1)
    # ------------------------------------------------------------------
    conclusion_blocks = list(
        text_blocks_qs.filter(
            placement=ReportTextBlock.Placement.CONCLUSION
        )
    )
    conclusion_num = next_top if conclusion_blocks else None

    # ------------------------------------------------------------------
    # Imagens (figuras contínuas, iguais ao showpage)
    # ------------------------------------------------------------------
    models_set = {o.__class__ for o in concrete_objects}
    ct_map = (
        ContentType.objects.get_for_models(*models_set)
        if models_set
        else {}
    )

    ids_by_ct = defaultdict(list)
    for o in concrete_objects:
        ct = ct_map.get(o.__class__)
        if ct:
            ids_by_ct[ct.id].append(o.pk)

    q = Q()
    for ct_id, ids in ids_by_ct.items():
        q |= Q(content_type_id=ct_id, object_id__in=ids)

    images_by_key = defaultdict(list)
    if q:
        imgs = (
            ObjectImage.objects
            .filter(q)
            .order_by("index", "id")
            .select_related("content_type")
        )
        for img in imgs:
            images_by_key[(img.content_type_id, img.object_id)].append(img)

    # ------------------------------------------------------------------
    # Monta outline UI (dict) + numeração contínua de figuras
    # ------------------------------------------------------------------
    figure_counter = 1
    outline_ui: list[dict] = []

    for g in outline:
        g_dict = asdict(g)
        g_objects_ui: list[dict] = []

        for o in g.objects:
            o_dict = asdict(o)
            obj = o.obj

            ct = ct_map.get(obj.__class__)
            ct_id = ct.id if ct else None

            images_ui = []
            if ct_id:
                for img in images_by_key.get((ct_id, obj.pk), []):
                    images_ui.append({
                        "img": img,
                        "figure_label": f"Figura {figure_counter}",
                    })
                    figure_counter += 1

            o_dict["images"] = images_ui
            g_objects_ui.append(o_dict)

        g_dict["objects"] = g_objects_ui
        outline_ui.append(g_dict)

    # ------------------------------------------------------------------
    # Render HTML
    # ------------------------------------------------------------------
    html = render_to_string(
        "report_maker/report_pdf.html",
        {
            "report": report,
            "header": report.header_context,   # 🔴 snapshot / FK correto
            "preamble": preamble,
            "outline": outline_ui,
            "conclusion_num": conclusion_num,
            "conclusion_blocks": conclusion_blocks,
            "is_pdf": True,
        },
        request=request,
    )

    base_url = request.build_absolute_uri("/")

    pdf_bytes = HTML(
        string=html,
        base_url=base_url,
    ).write_pdf(
        stylesheets=[
            CSS(url=f"{base_url}static/report_maker/css/report_print.css"),
            CSS(url=f"{base_url}static/report_maker/css/report_preview.css"),
        ]
    )

    filename = f"laudo_{report.report_number}".replace("/", "-").replace(".", "_")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}.pdf"'
    return response
