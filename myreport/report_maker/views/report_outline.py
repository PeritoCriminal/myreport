# myreport/report_maker/views/report_outline.py
from __future__ import annotations

import base64
import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from report_maker.models import ReportTextBlock
from report_maker.models.exam_base import ExamObjectGroup


def _with_dash(number: str) -> str:
    """Formata o prefixo numérico para exibição."""
    number = (number or "").strip()
    return f"{number}." if number else ""


def _join_number(*parts: object) -> str:
    """Compõe uma numeração hierárquica a partir de partes não vazias."""
    return ".".join(
        str(part).strip(". ")
        for part in parts
        if str(part).strip(". ")
    )


def _numbered(*parts: object, enabled: bool = True) -> str:
    """Retorna a numeração formatada para exibição."""
    if not enabled:
        return ""
    return _with_dash(_join_number(*parts))


def _split_markdown_h2_sections(md_text: str) -> list[tuple[str, str]]:
    """Divide um texto Markdown em sub-seções a partir de headings H2."""
    text = (md_text or "").strip()
    if not text:
        return []

    heading_re = re.compile(r"^\s*##\s+(?P<label>.+?)\s*$")
    lines = text.splitlines()

    found_heading = False
    sections: list[tuple[str, str]] = []
    current_label = ""
    buffer: list[str] = []

    for line in lines:
        match = heading_re.match(line)
        if match:
            found_heading = True
            buffered_text = "\n".join(buffer).strip()
            if buffered_text:
                sections.append((current_label, buffered_text))
            current_label = match.group("label").strip()
            buffer = []
            continue
        buffer.append(line)

    buffered_text = "\n".join(buffer).strip()
    if buffered_text:
        sections.append((current_label, buffered_text))

    return sections if found_heading else []


@dataclass(frozen=True)
class OutlineSection:
    number: str
    label: str
    text: str
    fmt: str
    kind: str = "section_field"
    maps_url: Optional[str] = None
    qr_data_uri: Optional[str] = None


@dataclass(frozen=True)
class OutlineObject:
    number: str
    obj: Any
    title: str
    sections: list[OutlineSection]


@dataclass(frozen=True)
class OutlineGroup:
    number: str
    group_key: str
    group_label: str
    intro_text: str
    objects: list[OutlineObject]


def _png_bytes_to_data_uri(png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _get_group_intro_map(text_blocks_qs: Iterable[ReportTextBlock]) -> dict[str, str]:
    intro_by_group: dict[str, str] = {}
    for tb in text_blocks_qs:
        if tb.placement == ReportTextBlock.Placement.OBJECT_GROUP_INTRO and tb.group_key:
            intro_by_group[tb.group_key] = (tb.body or "").strip()
    return intro_by_group


def _expand_markdown_headings(
    resolved: list[tuple[str, str, str, str, str | None, str | None]],
) -> list[tuple[str, str, str, str, str | None, str | None]]:
    expanded: list[tuple[str, str, str, str, str | None, str | None]] = []

    for kind, label, text, fmt, maps_url, qr_data_uri in resolved:
        fmt_normalized = (fmt or "").strip().lower()
        raw_text = text or ""

        if fmt_normalized == "markdown":
            fmt_normalized = "md"

        is_markdown_like = fmt_normalized == "md" or (
            fmt_normalized == "text" and bool(re.search(r"(?m)^\s*##\s+\S+", raw_text))
        )

        if not is_markdown_like:
            expanded.append((kind, label, text, fmt, maps_url, qr_data_uri))
            continue

        md_sections = _split_markdown_h2_sections(raw_text)
        if not md_sections:
            expanded.append((kind, label, text, fmt_normalized, maps_url, qr_data_uri))
            continue

        for idx, (md_label, md_text) in enumerate(md_sections):
            if not md_text.strip():
                continue

            if md_label:
                expanded.append(
                    ("markdown_heading", md_label, md_text, fmt_normalized, maps_url, qr_data_uri)
                )
                continue

            fallback_label = label if idx == 0 else ""
            expanded.append((kind, fallback_label, md_text, fmt_normalized, maps_url, qr_data_uri))

    return expanded


def build_report_outline(
    *,
    report,
    exam_objects_qs,
    text_blocks_qs,
    start_at: int = 1,
    prepend_blocks: list[dict] | None = None,
    append_blocks: list[dict] | None = None,
) -> tuple[list[OutlineGroup], int]:
    """
    Constrói a outline editorial do laudo, incluindo blocos virtuais iniciais
    e finais, objetos de exame agrupados e numeração hierárquica para exibição.
    """
    outline: list[OutlineGroup] = []
    n_top = start_at

    def _add_virtual_groups(block_list: list[dict], current_n: int) -> int:
        """Converte blocos virtuais em OutlineGroups numerados, com suporte a headings Markdown."""
        for b in block_list:
            kind = (b.get("kind") or "").strip()
            label = (b.get("label") or "").strip()
            if not label:
                continue

            text = ""
            fmt = (b.get("fmt") or "text").strip()

            if kind == "kv_section":
                items = b.get("items") or []
                lines = []
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    k = (it.get("label") or "").strip()
                    v = it.get("value")
                    if v is None:
                        continue
                    v_str = v.strftime("%d/%m/%Y %H:%M") if hasattr(v, "strftime") else str(v).strip()
                    if v_str:
                        lines.append(f"{k}: {v_str}" if k else v_str)
                text = "\n".join(lines).strip()

            elif kind == "text_section":
                text = (b.get("value") or "").strip()

            if label == "Objetivo" or not text:
                if not text:
                    continue

            resolved = _expand_markdown_headings([(kind, label, text, fmt, None, None)])

            out_sections: list[OutlineSection] = []

            if not resolved:
                out_sections.append(
                    OutlineSection(number="", label="", text=text, fmt=fmt)
                )
            else:
                base_number = str(current_n)
                child_index = 0
                first_section_consumed = False

                for sec_kind, sec_label, sec_text, sec_fmt, maps_url, qr_data_uri in resolved:
                    has_label = bool((sec_label or "").strip())

                    if not first_section_consumed:
                        first_section_consumed = True
                        out_sections.append(
                            OutlineSection(
                                number="",
                                label="",
                                text=sec_text,
                                fmt=sec_fmt,
                                kind=sec_kind,
                                maps_url=maps_url,
                                qr_data_uri=qr_data_uri,
                            )
                        )
                        continue

                    if sec_kind == "markdown_heading" and has_label:
                        child_index += 1
                        out_sections.append(
                            OutlineSection(
                                number=_numbered(base_number, child_index),
                                label=sec_label,
                                text=sec_text,
                                fmt=sec_fmt,
                                kind=sec_kind,
                                maps_url=maps_url,
                                qr_data_uri=qr_data_uri,
                            )
                        )
                        continue

                    out_sections.append(
                        OutlineSection(
                            number="",
                            label=sec_label if has_label else "",
                            text=sec_text,
                            fmt=sec_fmt,
                            kind=sec_kind,
                            maps_url=maps_url,
                            qr_data_uri=qr_data_uri,
                        )
                    )

            outline.append(
                OutlineGroup(
                    number="",
                    group_key="__VIRTUAL__",
                    group_label="",
                    intro_text="",
                    objects=[
                        OutlineObject(
                            number=_numbered(current_n),
                            obj=report,
                            title=label,
                            sections=out_sections,
                        )
                    ],
                )
            )
            current_n += 1

        return current_n

    if prepend_blocks:
        n_top = _add_virtual_groups(prepend_blocks, n_top)

    UNGROUPED = "__UNGROUPED__"
    GROUP_ORDER = [
        ExamObjectGroup.LOCATIONS,
        ExamObjectGroup.VEHICLES,
        ExamObjectGroup.PARTS,
        ExamObjectGroup.CADAVERS,
        ExamObjectGroup.OTHER,
    ]
    GROUP_RANK = {g.value: i for i, g in enumerate(GROUP_ORDER)}

    def _group_sort_key(gk: str) -> tuple[int, str]:
        if gk == UNGROUPED:
            return (9_500, "")
        if gk in GROUP_RANK:
            return (GROUP_RANK[gk], gk)
        return (9_000, gk)

    objects = [o.concrete for o in exam_objects_qs]
    grouped: OrderedDict[str, list[Any]] = OrderedDict()
    for obj in objects:
        gk = getattr(obj, "group_key", None) or UNGROUPED
        grouped.setdefault(gk, []).append(obj)

    intro_by_group = _get_group_intro_map(text_blocks_qs)

    for group_key in sorted(grouped.keys(), key=_group_sort_key):
        group_objs = grouped[group_key]
        use_header = group_key != UNGROUPED and (
            bool(intro_by_group.get(group_key)) or len(group_objs) >= 2
        )

        group_label = ExamObjectGroup(group_key).label if group_key in ExamObjectGroup.values else ""
        group_number = _numbered(n_top) if use_header else ""

        out_objs = []
        for n_obj, obj in enumerate(group_objs, 1):
            title_field = obj.get_object_title_field() if hasattr(obj, "get_object_title_field") else "title"
            title_value = (getattr(obj, title_field, "") or "").strip() or str(obj)
            obj_number = _numbered(n_top, n_obj) if use_header else _numbered(n_top)

            blocks = obj.get_render_blocks() if hasattr(obj, "get_render_blocks") else []
            resolved = []
            for b in blocks:
                if not isinstance(b, dict):
                    continue

                kind = b.get("kind", "").strip()
                label = b.get("label", "").strip()
                fmt = b.get("fmt", "text").strip()
                text = ""
                maps_url = None
                qr_data_uri = None

                if kind == "geo_location":
                    text = (getattr(obj, b.get("field", "geo_location"), "") or "").strip()
                    if text:
                        parser = getattr(obj, "parse_location_line", None)
                        if callable(parser):
                            data = parser(text) or {}
                            maps_url = data.get("maps_url")
                            if data.get("qrcode_png"):
                                qr_data_uri = _png_bytes_to_data_uri(data["qrcode_png"])
                elif kind == "section_field":
                    text = (getattr(obj, b.get("field", ""), "") or "").strip()
                elif kind == "render_section":
                    getter = getattr(obj, "get_section_value", None)
                    if callable(getter):
                        text = (getter(b.get("key")) or "").strip()

                if text:
                    resolved.append((kind, label, text, fmt, maps_url, qr_data_uri))

            resolved = _expand_markdown_headings(resolved)
            out_sections: list[OutlineSection] = []

            base_section_index = 0
            current_parent_number = ""
            markdown_child_index = 0

            for kind, label, text, fmt, maps_url, qr_data_uri in resolved:
                has_label = bool((label or "").strip())

                if kind == "markdown_heading":
                    if current_parent_number and has_label:
                        markdown_child_index += 1
                        out_sections.append(
                            OutlineSection(
                                _numbered(current_parent_number, markdown_child_index),
                                label,
                                text,
                                fmt,
                                kind,
                                maps_url,
                                qr_data_uri,
                            )
                        )
                    else:
                        base_section_index += 1
                        current_parent_number = (
                            _join_number(n_top, n_obj, base_section_index)
                            if use_header
                            else _join_number(n_top, base_section_index)
                        )
                        markdown_child_index = 0
                        out_sections.append(
                            OutlineSection(
                                _numbered(current_parent_number, enabled=has_label),
                                label if has_label else "",
                                text,
                                fmt,
                                kind,
                                maps_url,
                                qr_data_uri,
                            )
                        )
                    continue

                if has_label:
                    base_section_index += 1
                    current_parent_number = (
                        _join_number(n_top, n_obj, base_section_index)
                        if use_header
                        else _join_number(n_top, base_section_index)
                    )
                    markdown_child_index = 0
                    out_sections.append(
                        OutlineSection(
                            _numbered(current_parent_number),
                            label,
                            text,
                            fmt,
                            kind,
                            maps_url,
                            qr_data_uri,
                        )
                    )
                else:
                    out_sections.append(
                        OutlineSection(
                            "",
                            "",
                            text,
                            fmt,
                            kind,
                            maps_url,
                            qr_data_uri,
                        )
                    )

            out_objs.append(OutlineObject(obj_number, obj, title_value, out_sections))
            if not use_header:
                n_top += 1

        outline.append(
            OutlineGroup(
                group_number,
                str(group_key),
                group_label,
                intro_by_group.get(group_key, ""),
                out_objs,
            )
        )
        if use_header:
            n_top += 1

    if append_blocks:
        n_top = _add_virtual_groups(append_blocks, n_top)

    return outline, n_top