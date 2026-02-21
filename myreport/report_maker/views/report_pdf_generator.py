# report_maker/views/report_pdf_generator.py
from __future__ import annotations

import re

import mimetypes
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from weasyprint import CSS, HTML
from weasyprint.urls import default_url_fetcher

from report_maker.models import ReportCase, ReportTextBlock
from report_maker.models.images import ObjectImage
from report_maker.views.report_outline import build_report_outline


def _build_header_from_user(request) -> dict:
    """
    Monta o cabeçalho institucional a partir do vínculo ATUAL do usuário.

    Usado quando o laudo está editável (report.can_edit == True), pois o laudo ainda pode
    acompanhar o contexto vigente do autor (instituição/equipe/núcleo).
    """
    user = request.user

    # Vínculo institucional atual do usuário
    team = user.team
    nucleus = user.nucleus
    inst = user.institution

    name = (getattr(inst, "name", "") or "") if inst else ""
    acronym = (getattr(inst, "acronym", "") or "") if inst else ""

    if inst and hasattr(inst, "get_kind_display"):
        kind_display = inst.get_kind_display()
    else:
        kind_display = str(getattr(inst, "kind", "") or "") if inst else ""

    hon_title = (getattr(inst, "honoree_title", "") or "") if inst else ""
    hon_name = (getattr(inst, "honoree_name", "") or "") if inst else ""
    honoree_line = f"{hon_title} {hon_name}" if (hon_title and hon_name) else (hon_name or "")

    # ─────────────────────────────────────────────
    # Unit line (evita repetir núcleo/equipe)
    # ─────────────────────────────────────────────
    nucleus_txt = (getattr(nucleus, "name", "") or "").strip() if nucleus else ""
    team_txt = (getattr(team, "name", "") or "").strip() if team else ""

    team_is_redundant = False
    if team and getattr(team, "is_nucleus_team", False):
        team_is_redundant = True
    elif nucleus_txt and team_txt and nucleus_txt.casefold() == team_txt.casefold():
        team_is_redundant = True

    unit_parts = []
    if nucleus_txt:
        unit_parts.append(nucleus_txt)
    if team_txt and not team_is_redundant:
        unit_parts.append(team_txt)

    unit_line = " - ".join(unit_parts)

    return {
        "name": name or None,
        "acronym": acronym or None,
        "kind_display": kind_display or None,
        "honoree_line": honoree_line or None,
        "unit_line": unit_line or None,
        "emblem_primary": getattr(inst, "emblem_primary", None) if inst else None,
        "emblem_secondary": getattr(inst, "emblem_secondary", None) if inst else None,
    }


def _build_header_from_snapshots(report: ReportCase) -> dict:
    """
    Monta o cabeçalho institucional usando snapshots persistidos no ReportCase.

    Usado quando o laudo está concluído/bloqueado, garantindo coerência histórica:
    - mudanças futuras no vínculo do usuário não alteram o documento.
    """
    inst = report.institution  # fallback opcional para emblemas

    name = (report.institution_name_snapshot or "").strip()
    acronym = (report.institution_acronym_snapshot or "").strip()
    kind_display = (report.institution_kind_snapshot or "").strip()

    hon_title = (report.honoree_title_snapshot or "").strip()
    hon_name = (report.honoree_name_snapshot or "").strip()
    honoree_line = f"{hon_title} {hon_name}" if (hon_title and hon_name) else (hon_name or "")

    # ─────────────────────────────────────────────
    # Unit line (snapshot-safe) — evita repetir núcleo/equipe
    # ─────────────────────────────────────────────
    nucleus_txt = (report.nucleus_display or "").strip()
    team_txt = (report.team_display or "").strip()

    team_is_redundant = False
    if report.team and getattr(report.team, "is_nucleus_team", False):
        team_is_redundant = True
    elif nucleus_txt and team_txt and nucleus_txt.casefold() == team_txt.casefold():
        team_is_redundant = True

    unit_parts = []
    if nucleus_txt:
        unit_parts.append(nucleus_txt)
    if team_txt and not team_is_redundant:
        unit_parts.append(team_txt)

    unit_line = " - ".join(unit_parts)

    emblem_primary = report.emblem_primary_snapshot or (inst.emblem_primary if inst else None)
    emblem_secondary = report.emblem_secondary_snapshot or (inst.emblem_secondary if inst else None)

    return {
        "name": name or None,
        "acronym": acronym or None,
        "kind_display": kind_display or None,
        "honoree_line": honoree_line or None,
        "unit_line": unit_line or None,
        "emblem_primary": emblem_primary,
        "emblem_secondary": emblem_secondary,
    }


def django_url_fetcher(url: str):
    """
    URL fetcher para o WeasyPrint com suporte a /media/ e /static/.

    Por que existe:
    - O WeasyPrint resolve recursos (imagens/CSS/fonts) usando URLs.
    - Em desenvolvimento local (Windows/Linux) e em produção, os recursos podem
      chegar como:
        - "/media/..." (path relativo)
        - "http(s)://.../media/..." (url absoluta)
        - "/static/..." (path relativo)
        - "http(s)://.../static/..." (url absoluta)

    Estratégia:
    - Extrai o path da URL (parsed.path) e tenta resolver:
      1) /media/...   -> MEDIA_ROOT
      2) /static/...  -> django.contrib.staticfiles.finders
    - Se não resolver, cai no default_url_fetcher (http/https/file/...).

    Observação:
    - Retorna dict no formato esperado pelo WeasyPrint:
      {"file_obj": <file>, "mime_type": "...", "redirected_url": url}
    """
    parsed = urlparse(url)
    path = parsed.path or ""

    media_url = (getattr(settings, "MEDIA_URL", "") or "/media/").rstrip("/") + "/"
    static_url = (getattr(settings, "STATIC_URL", "") or "/static/").rstrip("/") + "/"

    def _open_file(file_path: Path):
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return {
            "file_obj": open(file_path, "rb"),
            "mime_type": mime_type or "application/octet-stream",
            "redirected_url": url,
        }

    # /media/... -> MEDIA_ROOT/...
    if path.startswith(media_url):
        rel = path[len(media_url):].lstrip("/")
        file_path = Path(settings.MEDIA_ROOT) / Path(*rel.split("/"))
        if file_path.exists():
            return _open_file(file_path)

    # /static/... -> encontra via finders
    if path.startswith(static_url):
        rel = path[len(static_url):].lstrip("/")
        found = finders.find(rel)
        if found:
            return _open_file(Path(found))

    return default_url_fetcher(url)


@login_required
def reportPDFGenerator(request, pk):
    """
    Gera o PDF do laudo via WeasyPrint.

    Controle de acesso:
    - usuário autenticado;
    - apenas o autor do laudo pode gerar o PDF (filtrado por author=request.user).

    Conceito:
    - PDF é artefato derivado; pode ser gerado a qualquer momento.
    - Quando o laudo está editável (report.can_edit == True), cabeçalho usa contexto atual do usuário.
    - Quando o laudo está concluído/bloqueado, cabeçalho usa snapshots do ReportCase.

    Observação:
    - A numeração de figuras (Figura 1, Figura 2, ...) é contínua no documento e é
      calculada aqui, porque depende do conjunto completo de imagens do laudo.
    """
    report = get_object_or_404(
        ReportCase.objects.select_related("author", "institution", "nucleus", "team"),
        pk=pk,
        author=request.user,
    )

    can_edit = bool(getattr(report, "can_edit", False))
    header = _build_header_from_user(request) if can_edit else _build_header_from_snapshots(report)

    text_blocks_qs = report.text_blocks.all().order_by("placement", "position", "created_at")

    # Preâmbulo: usuário > sistema
    preamble_text = (
        text_blocks_qs
        .filter(placement=ReportTextBlock.Placement.PREAMBLE)
        .values_list("body", flat=True)
        .first()
    )
    preamble = (preamble_text or "").strip() or report.preamble

    # Objetos do laudo (ordem global) + concretos (para ContentType/images)
    base_objects = list(report.exam_objects.all().order_by("order", "created_at"))
    concrete_objects = [o.concrete for o in base_objects]

    # ─────────────────────────────────────────────
    # PREPEND (mesma ordem do showpage)
    # Resumo, Sumário, Metadados
    # ─────────────────────────────────────────────
    meta_blocks = list(report.get_render_blocks() or [])
    prepend_blocks: list[dict] = []

    summary_text = (
        text_blocks_qs
        .filter(placement=ReportTextBlock.Placement.SUMMARY)
        .values_list("body", flat=True)
        .first()
    )
    if (summary_text or "").strip():
        prepend_blocks.append({
            "kind": "text_section",
            "label": "Resumo",
            "value": summary_text,
            "fmt": "md",
        })

    toc_text = (
        text_blocks_qs
        .filter(placement=ReportTextBlock.Placement.TOC)
        .values_list("body", flat=True)
        .first()
    )
    if (toc_text or "").strip():
        prepend_blocks.append({
            "kind": "text_section",
            "label": "Sumário",
            "value": toc_text,
            "fmt": "md",
        })

    prepend_blocks.extend(meta_blocks)

    outline, next_top = build_report_outline(
        report=report,
        exam_objects_qs=base_objects,
        text_blocks_qs=text_blocks_qs,
        start_at=1,
        prepend_blocks=prepend_blocks,
    )

    # Observações finais / Conclusão (numeração no nível superior)
    final_considerations_blocks = list(
        text_blocks_qs.filter(placement=ReportTextBlock.Placement.FINAL_CONSIDERATIONS)
    )
    final_considerations_num = next_top if final_considerations_blocks else None
    next_after_final = next_top + (1 if final_considerations_blocks else 0)

    conclusion_blocks = list(
        text_blocks_qs.filter(placement=ReportTextBlock.Placement.CONCLUSION)
    )
    conclusion_num = next_after_final if conclusion_blocks else None

    # ─────────────────────────────────────────────
    # Imagens em lote por ContentType do CONCRETO
    # ─────────────────────────────────────────────
    models_set = {o.__class__ for o in concrete_objects}
    ct_map = ContentType.objects.get_for_models(*models_set) if models_set else {}

    ids_by_ct = defaultdict(list)  # {ct_id: [uuid...]}
    for o in concrete_objects:
        ct = ct_map.get(o.__class__)
        if ct:
            ids_by_ct[ct.id].append(o.pk)

    q = Q()
    for ct_id, ids in ids_by_ct.items():
        q |= Q(content_type_id=ct_id, object_id__in=ids)

    images_by_key = defaultdict(list)  # {(ct_id, obj_id): [ObjectImage]}
    if q:
        imgs = (
            ObjectImage.objects
            .filter(q)
            .order_by("index", "id")
            .select_related("content_type")
        )
        for img in imgs:
            images_by_key[(img.content_type_id, img.object_id)].append(img)

    # ─────────────────────────────────────────────
    # Monta outline UI com figuras contínuas
    # ─────────────────────────────────────────────
    figure_counter = 1
    outline_ui: list[dict] = []

    for g in outline:
        g_dict = asdict(g)
        g_objects_ui: list[dict] = []

        for o in g.objects:
            o_dict = asdict(o)
            obj = o.obj  # concreto (ou ReportCase nos blocos prepend)

            if isinstance(obj, ReportCase):
                ct_id = None
            else:
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

    html = render_to_string(
        "report_maker/report_pdf.html",
        {
            "report": report,
            "header": header,
            "preamble": preamble,
            "outline": outline_ui,
            "final_considerations_num": final_considerations_num,
            "final_considerations_blocks": final_considerations_blocks,
            "conclusion_num": conclusion_num,
            "conclusion_blocks": conclusion_blocks,
            "is_pdf": True,
        },
        request=request,
    )

    css_path = finders.find("report_maker/css/report_pdf.css")
    if not css_path:
        # Este erro é de infraestrutura; não faz sentido devolver 404.
        raise FileNotFoundError("CSS do PDF não encontrado: report_maker/css/report_pdf.css")

    base_url = request.build_absolute_uri("/")

    pdf_bytes = HTML(
        string=html,
        base_url=base_url,
        url_fetcher=django_url_fetcher,
    ).write_pdf(stylesheets=[CSS(filename=css_path)])

    def normalize(value: str) -> str:
        # substitui / por _
        value = value.replace("/", "_")
        # remove tudo que não seja letra, número ou _
        value = re.sub(r"[^a-zA-Z0-9_]", "", value)
        return value.lower()

    number_part = normalize(report.report_number)
    type_part = normalize(report.criminal_typification)

    filename = f"{number_part}${type_part}"

    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    resp["X-Content-Type-Options"] = "nosniff"
    resp["Content-Length"] = str(len(pdf_bytes))
    return resp
