# myreport/report_maker/views/report_outline.py
from __future__ import annotations

import base64
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from report_maker.models import ReportTextBlock
from report_maker.models.exam_base import ExamObjectGroup


def _with_dash(number: str) -> str:
    """
    Formata o prefixo numérico para exibição, inserindo " - " entre
    a numeração e o texto quando houver numeração.

    Ex.:
      "4" -> "4 -"
      "3.1.2" -> "3.1.2 -"
      "" -> ""
    """
    number = (number or "").strip()
    return f"{number} -" if number else ""


@dataclass(frozen=True)
class OutlineSection:
    """
    Sub-seção renderizável dentro de um objeto do laudo.

    Campos:
    - number: numeração hierárquica (ex.: "3.1.2 -") ou "" quando omitida por regra editorial.
    - label:  rótulo da seção (ex.: "Elementos Observados") ou "" quando renderização “inline”.
    - text:   conteúdo textual da seção.
    - fmt:    formato do texto: "text" | "md" | "kv".
    - kind:   tipo de seção:
        - "section_field": texto vindo de um field do model;
        - "render_section": texto vindo de getter/serviço do objeto;
        - "geo_location": campo especial que pode gerar maps_url e QR.
    - maps_url: URL pronta para abrir no Google Maps (quando kind == "geo_location").
    - qr_data_uri: PNG (data URI) do QR Code do Maps (quando disponível).
    """
    number: str
    label: str
    text: str
    fmt: str  # "text" | "md" | "kv"
    kind: str = "section_field"  # "section_field" | "render_section" | "geo_location"
    maps_url: Optional[str] = None
    qr_data_uri: Optional[str] = None


@dataclass(frozen=True)
class OutlineObject:
    """
    Um objeto do laudo (instância concreta de ExamObject ou similar), já pronto para render.

    Campos:
    - number: numeração do objeto (ex.: "3.1 -" ou "4 -" quando não há cabeçalho de grupo).
    - obj: instância concreta (usada no showpage para puxar imagens, ids, etc.).
    - title: título do objeto (derivado do field indicado por get_object_title_field()).
    - sections: lista de OutlineSection já filtradas e numeradas.
    """
    number: str
    obj: Any
    title: str
    sections: list[OutlineSection]


@dataclass(frozen=True)
class OutlineGroup:
    """
    Agrupamento editorial de objetos do laudo.

    Um grupo pode ter cabeçalho (T1) ou não:
    - number == "" -> grupo sem cabeçalho (objetos aparecem direto no nível superior).
    - number != "" -> grupo com cabeçalho (objetos numerados como n_top.n_obj).

    Campos:
    - number: numeração do cabeçalho do grupo (ex.: "3 -") ou "".
    - group_key: chave do grupo (enum ExamObjectGroup.value) ou "" para "sem grupo".
    - group_label: rótulo humano do grupo.
    - intro_text: texto introdutório do grupo (ReportTextBlock OBJECT_GROUP_INTRO), se existir.
    - objects: lista de OutlineObject.
    """
    number: str
    group_key: str
    group_label: str
    intro_text: str
    objects: list[OutlineObject]


def _png_bytes_to_data_uri(png_bytes: bytes) -> str:
    """Converte bytes PNG em data URI para embutir no HTML/PDF sem arquivo separado."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _get_group_intro_map(text_blocks_qs: Iterable[ReportTextBlock]) -> dict[str, str]:
    """
    Mapeia group_key -> body do texto introdutório do grupo, quando existir.

    Considera apenas:
    - placement == OBJECT_GROUP_INTRO
    - group_key preenchido
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
    Constrói a OUTLINE editorial do laudo (estrutura única para showpage/preview/pdf).

    O que esta função entrega:
    - outline: lista de OutlineGroup, cada um contendo objetos e suas seções prontas para render;
    - next_top: próximo número “T1” disponível após renderizar toda a outline.

    Entradas:
    - report: ReportCase do laudo.
    - exam_objects_qs: queryset/lista dos objetos do exame (ordem já definida pelo laudo).
      Importante: cada item deve expor `.concrete` (instância concreta do ExamObject).
    - text_blocks_qs: textos do laudo (ReportTextBlock) usados para:
        - intros de grupo (OBJECT_GROUP_INTRO)
        - outros placements não são consumidos aqui (somente enviados pela view via prepend_blocks).
    - start_at: número inicial do contador de nível superior (padrão: 1).
    - prepend_blocks: blocos iniciais do laudo (Resumo, Sumário, metadados etc.).
      Estes blocos são convertidos em “grupos virtuais” com um único objeto (obj=report),
      usando numeração de nível superior.

    Regras editoriais importantes:
    0) Blocos iniciais (prepend_blocks):
       - viram entradas T1 (number="1 -", "2 -", "3 -"...), SEM subdivisões (sem "1.1").
       - "Objetivo" só é renderizado se houver conteúdo.
    1) Agrupamento dos objetos:
       - group_key None/"" -> UNGROUPED (sem cabeçalho de grupo).
       - grupos “conhecidos” seguem ordem fixa (LOCATIONS, VEHICLES, PARTS, CADAVERS, OTHER).
       - grupos inesperados entram por fallback, mantendo previsibilidade.
    2) Cabeçalho de grupo (T1) só aparece se:
       - houver intro_text para o grupo, OU
       - o grupo tiver 2+ objetos.
       Caso contrário, objetos do grupo aparecem direto no nível superior (T1).
    3) Subtítulos (seções dentro de um objeto):
       - se o objeto tem apenas 1 seção preenchida, o rótulo e numeração da seção são omitidos
         (render “inline”), para evitar subtítulo inútil.
       - exceção: geo_location sozinho pode manter label (melhor UX e legibilidade).
    4) Numeração:
       - com cabeçalho de grupo:
           Grupo: n_top
           Objeto: n_top.n_obj
           Seção: n_top.n_obj.n_sec
       - sem cabeçalho de grupo:
           Objeto: n_top
           Seção: n_top.n_sec

    Observação:
    - Esta função não lida com imagens. As views (showpage/pdf) fazem isso em lote
      para manter performance e controle de “Figura X”.
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
    # 0) Blocos iniciais do laudo (metadados) como T1 (SEM "Dados do Laudo")
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

                    # datetime/date -> formata aqui para padronizar saída
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

            # Só renderiza "Objetivo" se tiver conteúdo
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
                            number=_with_dash(f"{n_top}"),
                            obj=report,
                            title=label,
                            sections=[
                                OutlineSection(
                                    number="",  # não cria "1.1"
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
    # 1) Objetos do exame + regra global de subtítulos
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
        group_number = _with_dash(f"{n_top}") if use_header else ""

        out_objs: list[OutlineObject] = []
        n_obj = 1

        for obj in group_objs:
            title_field = obj.get_object_title_field() if hasattr(obj, "get_object_title_field") else "title"
            title_value = (getattr(obj, title_field, "") or "").strip() or str(obj)

            raw_obj_number = f"{n_top}.{n_obj}" if use_header else f"{n_top}"
            obj_number = _with_dash(raw_obj_number)

            blocks = obj.get_render_blocks() if hasattr(obj, "get_render_blocks") else []

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
                        # não quebra a outline se vier entrada ruim
                        pass

                elif kind == "section_field":
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

            # Regra global de “subtítulo”
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

                    raw_sec_number = f"{n_top}.{n_obj}.{n_sec}" if use_header else f"{n_top}.{n_sec}"
                    sec_number = _with_dash(raw_sec_number)
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

            # Se não existe cabeçalho de grupo, cada objeto “consome” um T1
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

        # Se existe cabeçalho de grupo, o grupo “consome” um T1 ao final
        if use_header:
            n_top += 1

    return outline, n_top
