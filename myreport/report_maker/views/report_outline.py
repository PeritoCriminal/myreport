# report_maker/views/report_outline.py

from __future__ import annotations

import base64
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from report_maker.models import ReportTextBlock
from report_maker.models.exam_base import ExamObjectGroup


@dataclass(frozen=True)
class OutlineSection:
    number: str
    label: str
    text: str
    fmt: str  # "text" | "md" | "kv"
    kind: str = "section_field"  # "section_field" | "render_section" | "geo_location"
    maps_url: Optional[str] = None
    qr_data_uri: Optional[str] = None


@dataclass(frozen=True)
class OutlineObject:
    number: str
    obj: Any  # instância concreta
    title: str
    sections: list[OutlineSection]


@dataclass(frozen=True)
class OutlineGroup:
    number: str  # pode ser "" quando não há cabeçalho de grupo
    group_key: str
    group_label: str
    intro_text: str
    objects: list[OutlineObject]


def _png_bytes_to_data_uri(png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _get_group_intro_map(text_blocks_qs: Iterable[ReportTextBlock]) -> dict[str, str]:
    """
    Mapeia group_key -> body do texto introdutório do grupo, quando existir.
    """
    intro_by_group: dict[str, str] = {}
    for tb in text_blocks_qs:
        if tb.placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO and tb.group_key:
            intro_by_group[tb.group_key] = (tb.body or "").strip()
    return intro_by_group


def build_report_outline(
    *,
    report,
    exam_objects_qs,
    text_blocks_qs,
    start_at: int = 1,
    prepend_blocks: list[dict] | None = None,
) -> tuple[list[OutlineGroup], int]:
    """
    (docstring mantida)
    """
    UNGROUPED = "__UNGROUPED__"

        # Ordem editorial fixa dos grupos (laudo)
    GROUP_ORDER = [
        ExamObjectGroup.LOCATIONS,
        ExamObjectGroup.VEHICLES,
        ExamObjectGroup.PARTS,
        ExamObjectGroup.CADAVERS,
        ExamObjectGroup.OTHER,  # sempre por último
    ]
    GROUP_RANK = {g.value: i for i, g in enumerate(GROUP_ORDER)}

    def _group_sort_key(gk: str) -> tuple[int, str]:
        # UNGROUPED: objetos "sem grupo" (T1 direto) -> penúltimos, antes de "Outros"
        if gk == UNGROUPED:
            return (9_500, "")

        # grupos conhecidos pela enum -> ordem fixa
        if gk in GROUP_RANK:
            return (GROUP_RANK[gk], gk)

        # fallback (caso apareça algum grupo futuro/inesperado)
        return (9_000, gk)


    outline: list[OutlineGroup] = []
    n_top = start_at  # contador de nível superior

    # ------------------------------------------------------------------
    # 0) Blocos iniciais do laudo (metadados) como T1/T2/T3 (SEM "Dados do Laudo")
    # ------------------------------------------------------------------
    if prepend_blocks:
        pblocks = [b for b in prepend_blocks if isinstance(b, dict)]
        for b in pblocks:
            kind = (b.get("kind") or "").strip()
            label = (b.get("label") or "").strip()
            if not label:
                continue

            text = ""
            fmt = "text"

            if kind == "kv_section":
                items = b.get("items") or []
                lines: list[str] = []
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    k = (it.get("label") or "").strip()
                    v = it.get("value")
                    if v is None:
                        continue

                    # datetime/date -> formata já aqui
                    if hasattr(v, "strftime"):
                        v_str = v.strftime("%d/%m/%Y %H:%M")
                    else:
                        v_str = str(v).strip()

                    if not v_str:
                        continue
                    lines.append(f"{k}: {v_str}" if k else v_str)

                text = "\n".join(lines).strip()
                fmt = (b.get("fmt") or "kv").strip()

            elif kind == "text_section":
                text = (b.get("value") or "").strip()
                fmt = (b.get("fmt") or "text").strip()

            # ✅ Só renderiza "Objetivo" se tiver conteúdo (não None e não "")
            if label == "Objetivo" and not text:
                continue

            if not text:
                continue

            outline.append(
                OutlineGroup(
                    number="",
                    group_key="__REPORT__",
                    group_label="",
                    intro_text="",
                    objects=[
                        OutlineObject(
                            number=f"{n_top}",
                            obj=report,
                            title=label,
                            sections=[
                                OutlineSection(
                                    number="",  # ✅ não mostra 1.1 / 2.1 / 3.1
                                    label="",
                                    text=text,
                                    fmt=fmt,
                                )
                            ],
                        )
                    ],
                )
            )
            n_top += 1

    # ------------------------------------------------------------------
    # 1) Objetos do exame (mantém lógica original) + regra global de subtítulos
    # ------------------------------------------------------------------
    objects = [o.concrete for o in exam_objects_qs]

    def _normalize_group_key(raw: Any) -> Any:
        if raw is None:
            return UNGROUPED
        if isinstance(raw, str):
            raw = raw.strip()
            return raw or UNGROUPED
        return raw or UNGROUPED

    grouped: "OrderedDict[str, list[Any]]" = OrderedDict()
    for obj in objects:
        raw_gk = getattr(obj, "group_key", None)
        gk = _normalize_group_key(raw_gk)
        grouped.setdefault(gk, []).append(obj)

    intro_by_group = _get_group_intro_map(text_blocks_qs)
    group_counts = {k: len(v) for k, v in grouped.items()}

    def group_has_header(group_key: str) -> bool:
        if group_key == UNGROUPED:
            return False
        if (intro_by_group.get(group_key) or "").strip():
            return True
        return group_counts.get(group_key, 0) >= 2

    for group_key in sorted(grouped.keys(), key=_group_sort_key):
        group_objs = grouped[group_key]
        use_header = group_has_header(group_key)

        if group_key == UNGROUPED:
            group_label = ""
        else:
            group_label = (
                ExamObjectGroup(group_key).label
                if group_key in ExamObjectGroup.values
                else str(group_key)
            )

        intro_text = intro_by_group.get(group_key, "") if group_key != UNGROUPED else ""
        group_number = f"{n_top}" if use_header else ""

        out_objs: list[OutlineObject] = []
        n_obj = 1

        for obj in group_objs:
            title_field = obj.get_object_title_field() if hasattr(obj, "get_object_title_field") else "title"
            title_value = (getattr(obj, title_field, "") or "").strip() or str(obj)

            obj_number = f"{n_top}.{n_obj}" if use_header else f"{n_top}"

            blocks = obj.get_render_blocks() if hasattr(obj, "get_render_blocks") else []

            # 1) Resolve textos e filtra só as seções preenchidas
            # (kind, label, text, fmt, maps_url, qr_data_uri)
            resolved: list[tuple[str, str, str, str, str | None, str | None]] = []

            for b in blocks:
                if not isinstance(b, dict):
                    continue

                kind = (b.get("kind") or "").strip()
                label = (b.get("label") or "").strip()
                fmt = (b.get("fmt") or "text").strip()

                text = ""
                maps_url: str | None = None
                qr_data_uri: str | None = None

                if kind == "geo_location":
                    field = b.get("field") or b.get("field_name") or "geo_location"
                    raw = (getattr(obj, field, "") or "").strip()
                    if not raw:
                        continue

                    text = raw
                    fmt = "text"

                    try:
                        parser = getattr(obj, "parse_location_line", None)
                        if callable(parser):
                            data = parser(raw) or {}
                            maps_url = data.get("maps_url")
                            png = data.get("qrcode_png")
                            if png:
                                qr_data_uri = _png_bytes_to_data_uri(png)
                    except Exception:
                        # não quebra o outline se vier entrada ruim
                        pass

                elif kind == "section_field":
                    # compatível com "field" e "field_name"
                    field = b.get("field") or b.get("field_name")
                    if field:
                        text = (getattr(obj, field, "") or "").strip()

                elif kind == "render_section":
                    key = b.get("key")
                    getter = getattr(obj, "get_section_value", None)
                    if key and callable(getter):
                        text = (getter(key) or "").strip()

                if not text:
                    continue

                resolved.append((kind, label, text, fmt, maps_url, qr_data_uri))

            # 2) Regra global:
            #    - se só 1 seção preenchida => NÃO renderiza label/número de seção (inline)
            #      EXCEÇÃO: geo_location sozinho mantém label (melhor UX)
            out_sections: list[OutlineSection] = []

            if len(resolved) == 1:
                kind, label, text, fmt, maps_url, qr_data_uri = resolved[0]
                keep_label = (kind == "geo_location" and bool(label.strip()))

                out_sections.append(
                    OutlineSection(
                        number="",
                        label=label if keep_label else "",
                        text=text,
                        fmt=fmt,
                        kind=kind,
                        maps_url=maps_url,
                        qr_data_uri=qr_data_uri,
                    )
                )
            else:
                n_sec = 1
                for kind, label, text, fmt, maps_url, qr_data_uri in resolved:
                    # se não tiver label, não cria "título" de seção (evita subtítulo vazio)
                    if not (label or "").strip():
                        out_sections.append(
                            OutlineSection(
                                number="",
                                label="",
                                text=text,
                                fmt=fmt,
                                kind=kind,
                                maps_url=maps_url,
                                qr_data_uri=qr_data_uri,
                            )
                        )
                        continue

                    sec_number = f"{n_top}.{n_obj}.{n_sec}" if use_header else f"{n_top}.{n_sec}"
                    out_sections.append(
                        OutlineSection(
                            number=sec_number,
                            label=label,
                            text=text,
                            fmt=fmt,
                            kind=kind,
                            maps_url=maps_url,
                            qr_data_uri=qr_data_uri,
                        )
                    )
                    n_sec += 1

            out_objs.append(
                OutlineObject(
                    number=obj_number,
                    obj=obj,
                    title=title_value,
                    sections=out_sections,
                )
            )
            n_obj += 1

            if not use_header:
                n_top += 1

        outline.append(
            OutlineGroup(
                number=group_number,
                group_key=("" if group_key == UNGROUPED else str(group_key)),
                group_label=group_label,
                intro_text=intro_text,
                objects=out_objs,
            )
        )

        if use_header:
            n_top += 1

    return outline, n_top
