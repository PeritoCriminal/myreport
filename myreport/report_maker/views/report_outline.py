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
    fmt: str  # "text" | "md"


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


def build_report_outline(*, report, exam_objects_qs, text_blocks_qs, start_at: int = 1) -> list[OutlineGroup]:
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

    O model define a estrutura (get_render_blocks). A view decide a profundidade (com/sem grupo).
    """
    # Downcast para o concreto (você já tem .concrete no ExamObject)
    objects = [o.concrete for o in exam_objects_qs]

    # Agrupa mantendo a ordem de aparição no laudo
    grouped: "OrderedDict[str, list[Any]]" = OrderedDict()
    for obj in objects:
        gk = getattr(obj, "group_key", ExamObjectGroup.OTHER) or ExamObjectGroup.OTHER
        grouped.setdefault(gk, []).append(obj)

    intro_by_group = _get_group_intro_map(text_blocks_qs)

    # Regra para “ativar” cabeçalho de grupo:
    # - mais de 1 grupo, OU
    # - existe texto introdutório para algum grupo
    use_group_headers = (len(grouped) > 1) or any(intro_by_group.values())

    outline: list[OutlineGroup] = []
    n_top = start_at  # contador de nível superior

    for group_key, group_objs in grouped.items():
        group_label = ExamObjectGroup(group_key).label if group_key in ExamObjectGroup.values else str(group_key)
        intro_text = intro_by_group.get(group_key, "")

        group_number = f"{n_top}" if use_group_headers else ""

        out_objs: list[OutlineObject] = []
        n_obj = 1

        for obj in group_objs:
            # título do objeto
            title_field = obj.get_object_title_field() if hasattr(obj, "get_object_title_field") else "title"
            title_value = (getattr(obj, title_field, "") or "").strip() or str(obj)

            if use_group_headers:
                obj_number = f"{n_top}.{n_obj}"
            else:
                obj_number = f"{n_top}"

            # seções (label = título abaixo; conteúdo = texto normal)
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

                if use_group_headers:
                    sec_number = f"{n_top}.{n_obj}.{n_sec}"
                else:
                    sec_number = f"{n_top}.{n_sec}"

                out_sections.append(OutlineSection(number=sec_number, label=label, text=text, fmt=fmt))
                n_sec += 1

            out_objs.append(OutlineObject(number=obj_number, obj=obj, title=title_value, sections=out_sections))
            n_obj += 1

            if not use_group_headers:
                # sem grupos, cada objeto consome um número de nível superior
                n_top += 1

        outline.append(
            OutlineGroup(
                number=group_number,
                group_key=group_key,
                group_label=group_label,
                intro_text=intro_text,
                objects=out_objs,
            )
        )

        if use_group_headers:
            # com grupos, cada grupo consome um número de nível superior
            n_top += 1

    return outline
