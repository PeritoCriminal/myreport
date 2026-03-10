# myreport/report_maker/views/report_case_showpage.py
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.views.generic import DetailView

from report_maker.models import ReportCase, ReportTextBlock
from report_maker.models.images import ObjectImage
from report_maker.views.report_outline import build_report_outline


class ReportCaseShowPageView(LoginRequiredMixin, DetailView):
    model = ReportCase
    template_name = "report_maker/reportcase_showpage.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(author=self.request.user)
            .select_related("institution", "nucleus", "team", "author")
        )

    # ─────────────────────────────────────────────────────────────
    # Header builders (mantidos conforme sua lógica original)
    # ─────────────────────────────────────────────────────────────
    def _build_header_from_user(self) -> dict:
        user = self.request.user
        team, nucleus, inst = user.team, user.nucleus, user.institution
        name = getattr(inst, "name", "") or ""
        acronym = getattr(inst, "acronym", "") or ""
        kind_display = inst.get_kind_display() if inst and hasattr(inst, "get_kind_display") else str(getattr(inst, "kind", "") or "")
        hon_title, hon_name = getattr(inst, "honoree_title", "") or "", getattr(inst, "honoree_name", "") or ""
        honoree_line = f"{hon_title} {hon_name}" if hon_title and hon_name else (hon_name or "")
        
        nucleus_txt = (getattr(nucleus, "name", "") or "").strip() if nucleus else ""
        team_txt = (getattr(team, "name", "") or "").strip() if team else ""
        team_is_redundant = (team and getattr(team, "is_nucleus_team", False)) or (nucleus_txt.casefold() == team_txt.casefold())
        
        unit_parts = [nucleus_txt] if nucleus_txt else []
        if team_txt and not team_is_redundant: unit_parts.append(team_txt)

        return {
            "name": name or None,
            "acronym": acronym or None,
            "kind_display": kind_display or None,
            "honoree_line": honoree_line or None,
            "unit_line": " - ".join(unit_parts) or None,
            "emblem_primary": getattr(inst, "emblem_primary", None) if inst else None,
            "emblem_secondary": getattr(inst, "emblem_secondary", None) if inst else None,
        }

    def _build_header_from_snapshots(self, report: ReportCase) -> dict:
        inst = report.institution
        hon_title, hon_name = (report.honoree_title_snapshot or "").strip(), (report.honoree_name_snapshot or "").strip()
        honoree_line = f"{hon_title} {hon_name}" if hon_title and hon_name else (hon_name or "")
        
        nucleus_txt, team_txt = (report.nucleus_display or "").strip(), (report.team_display or "").strip()
        team_is_redundant = (report.team and getattr(report.team, "is_nucleus_team", False)) or (nucleus_txt.casefold() == team_txt.casefold())
        
        unit_parts = [nucleus_txt] if nucleus_txt else []
        if team_txt and not team_is_redundant: unit_parts.append(team_txt)

        return {
            "name": (report.institution_name_snapshot or "").strip() or None,
            "acronym": (report.institution_acronym_snapshot or "").strip() or None,
            "kind_display": (report.institution_kind_snapshot or "").strip() or None,
            "honoree_line": honoree_line or None,
            "unit_line": " - ".join(unit_parts) or None,
            "emblem_primary": report.emblem_primary_snapshot or (inst.emblem_primary if inst else None),
            "emblem_secondary": report.emblem_secondary_snapshot or (inst.emblem_secondary if inst else None),
        }

    # ─────────────────────────────────────────────────────────────
    # Context
    # ─────────────────────────────────────────────────────────────
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # 1. Cabeçalho e Preâmbulo (Essencial para o topo do laudo)
        can_edit = bool(getattr(report, "can_edit", False))
        header = self._build_header_from_user() if can_edit else self._build_header_from_snapshots(report)

        text_blocks_qs = report.text_blocks.all().order_by("placement", "position", "created_at")
        
        preamble_text = text_blocks_qs.filter(placement=ReportTextBlock.Placement.PREAMBLE).values_list("body", flat=True).first()
        preamble = (preamble_text or "").strip() or report.preamble

        # 2. Preparação dos Blocos da Outline (Prepend / Append)
        prepend_blocks = []
        append_blocks = []

        # -- Prepend: Resumo, Glossário, Sumário, Histórico
        placements = ReportTextBlock.Placement
        def add_to_prepend(label, placement_enum):
            txt = text_blocks_qs.filter(placement=placement_enum).values_list("body", flat=True).first()
            if (txt or "").strip():
                prepend_blocks.append({"kind": "text_section", "label": label, "value": txt, "fmt": "md"})

        add_to_prepend("Resumo", placements.SUMMARY)
        
        glossary_p = getattr(placements, "GLOSSARY", None)
        if glossary_p: add_to_prepend("Glossário", glossary_p)
        
        add_to_prepend("Sumário", placements.TOC)
        
        history_p = getattr(placements, "HISTORY", None)
        if history_p: add_to_prepend("Histórico", history_p)

        # -- Metadados (Objetivo, etc)
        meta_blocks = list(report.get_render_blocks() or [])
        prepend_blocks.extend(meta_blocks)

        # -- Append: Considerações Finais e Conclusão
        cf_txt = "\n\n".join(text_blocks_qs.filter(placement=placements.FINAL_CONSIDERATIONS).values_list("body", flat=True))
        if cf_txt.strip():
            append_blocks.append({"kind": "text_section", "label": "Considerações Finais", "value": cf_txt, "fmt": "md"})

        c_txt = "\n\n".join(text_blocks_qs.filter(placement=placements.CONCLUSION).values_list("body", flat=True))
        if c_txt.strip():
            append_blocks.append({"kind": "text_section", "label": "Conclusão", "value": c_txt, "fmt": "md"})

        # 3. Construção da Outline
        base_objects = list(report.exam_objects.all().order_by("order", "created_at"))
        outline, next_top = build_report_outline(
            report=report,
            exam_objects_qs=base_objects,
            text_blocks_qs=text_blocks_qs,
            start_at=1,
            prepend_blocks=prepend_blocks,
            append_blocks=append_blocks,
        )

        # 4. Imagens e Figuras (Mantido conforme original)
        concrete_objects = [o.concrete for o in base_objects]
        models_set = {o.__class__ for o in concrete_objects}
        ct_map = ContentType.objects.get_for_models(*models_set) if models_set else {}
        
        ids_by_ct = defaultdict(list)
        for o in concrete_objects:
            ct = ct_map.get(o.__class__)
            if ct: ids_by_ct[ct.id].append(o.pk)

        q = Q()
        for ct_id, ids in ids_by_ct.items(): q |= Q(content_type_id=ct_id, object_id__in=ids)

        images_by_key = defaultdict(list)
        if q:
            imgs = ObjectImage.objects.filter(q).order_by("index", "id").select_related("content_type")
            for img in imgs: images_by_key[(img.content_type_id, img.object_id)].append(img)

        figure_counter = 1
        outline_ui = []
        for g in outline:
            g_dict = asdict(g)
            g_objs_ui = []
            for o in g.objects:
                o_dict = asdict(o)
                obj = o.obj
                ct_id = None if isinstance(obj, ReportCase) else getattr(ct_map.get(obj.__class__), "id", None)
                
                images_ui = []
                if ct_id:
                    for img in images_by_key.get((ct_id, obj.pk), []):
                        images_ui.append({"img": img, "figure_label": f"Figura {figure_counter}"})
                        figure_counter += 1
                o_dict["images"] = images_ui
                g_objs_ui.append(o_dict)
            g_dict["objects"] = g_objs_ui
            outline_ui.append(g_dict)

        # 5. Update final do contexto
        ctx.update({
            "header": header,
            "preamble": preamble,
            "outline": outline_ui,
            "next_top": next_top,
            "report_number": report.report_number,
        })
        return ctx