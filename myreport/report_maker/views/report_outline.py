# report_maker/views/report_outline.py

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Iterable

from report_maker.models import ReportTextBlock
from report_maker.models.exam_base import ExamObjectGroup


@dataclass(frozen=True)
class OutlineSection:
    number: str
    label: str
    text: str
    fmt: str  # "text" | "md" | "kv"


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
    Monta uma estrutura pronta para renderização:

    - Se houver cabeçalho de grupo:
        4 - Veículos
        4.1 - Honda Fit
        4.1.1 - Identificação
        4.1.2 - Testes operacionais

    - Se NÃO houver cabeçalho de grupo:
        4 - Honda Fit
        4.1 - Identificação
        4.2 - Testes operacionais

    Regras:
    - Cabeçalho de grupo só aparece quando o grupo "agrupar" de fato:
        * houver 2+ objetos no mesmo group_key, OU
        * existir texto introdutório (OBJECT_GROUP_INTRO) para aquele group_key.
    - Objetos "genéricos"/sem classificação podem vir com group_key vazio (None/""):
        * NÃO geram cabeçalho,
        * cada objeto consome um número de nível superior (T1).

    prepend_blocks:
    - Lista de blocos (sem numeração) para entrar antes dos objetos e participar da numeração.
      Use: report.get_render_blocks() (Dados da Requisição / Atendimento / Objetivo)

    Retorna:
        (outline, next_top)
        - next_top é o próximo número disponível de nível superior (T1), útil para Conclusão.
    """
    UNGROUPED = "__UNGROUPED__"

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
                                    number="",     # ✅ não mostra 1.1 / 2.1 / 3.1
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
    # 1) Objetos do exame (mantém lógica original)
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

    for group_key, group_objs in grouped.items():
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
            out_sections: list[OutlineSection] = []

            n_sec = 1
            for b in blocks:
                kind = (b.get("kind") or "").strip()
                label = (b.get("label") or "").strip()
                fmt = (b.get("fmt") or "text").strip()

                if not label:
                    continue

                text = ""

                if kind == "section_field":
                    field = b.get("field")
                    if field:
                        text = (getattr(obj, field, "") or "").strip()

                elif kind == "render_section":
                    key = b.get("key")
                    getter = getattr(obj, "get_section_value", None)
                    if key and callable(getter):
                        text = (getter(key) or "").strip()

                if not text:
                    continue

                sec_number = f"{n_top}.{n_obj}.{n_sec}" if use_header else f"{n_top}.{n_sec}"

                out_sections.append(
                    OutlineSection(
                        number=sec_number,
                        label=label,
                        text=text,
                        fmt=fmt,
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
