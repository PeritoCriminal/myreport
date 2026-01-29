# report_maker/views/report_pdf_generator.py
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from weasyprint import HTML, CSS

from report_maker.models import ReportCase
from report_maker.models.images import ObjectImage
from report_maker.views.report_outline import build_report_outline


@login_required
def reportPDFGenerator(request, pk):
    report = get_object_or_404(
        ReportCase.objects.select_related("author"),
        pk=pk,
    )

    # Mesmo padrão do detail: imagens ordenadas e prefetched
    images_qs = ObjectImage.objects.order_by("index", "id")

    exam_objects_qs = (
        report.exam_objects.all()
        .prefetch_related("images")
        .order_by("order", "created_at")
    )

    text_blocks_qs = report.text_blocks.all().order_by("placement", "position", "created_at")

    outline, next_top = build_report_outline(
        report=report,
        exam_objects_qs=exam_objects_qs,
        text_blocks_qs=text_blocks_qs,
        start_at=1,
    )

    html = render_to_string(
        "report_maker/report_pdf.html",
        {
            "report": report,
            "outline": outline,
            "next_top": next_top,
            "is_pdf": True,
        },
        request=request,
    )

    base_url = request.build_absolute_uri("/")  # resolve /static/

    pdf_bytes = HTML(string=html, base_url=base_url).write_pdf(
        stylesheets=[
            CSS(url=f"{base_url}static/report_maker/css/report_print.css"),
            CSS(url=f"{base_url}static/report_maker/css/report_preview.css"),
        ]
    )

    filename = f"laudo_{report.report_number}.pdf".replace("/", "-").replace(".", "_")
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp
