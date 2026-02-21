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
    """
    Renderização “showpage” do laudo (HTML em formato de documento).

    Controle de acesso:
    - usuário autenticado;
    - apenas o autor do laudo (filtrado em get_queryset).

    Regras de cabeçalho:
    - Se o laudo estiver editável (report.can_edit == True), o cabeçalho é montado a partir do
      contexto ATUAL do usuário (vínculo institucional/Equipe/Núcleo).
    - Se o laudo estiver concluído/bloqueado, o cabeçalho é montado a partir dos snapshots
      armazenados no próprio ReportCase, garantindo consistência histórica.

    Conteúdo:
    - Textos do laudo vêm de ReportTextBlock, agrupados por placement.
    - O preâmbulo prioriza o bloco PREAMBLE do usuário; se vazio, usa report.preamble.
    - A outline do laudo é construída por build_report_outline(), com blocos iniciais (Resumo,
      Glossário, Sumário e metadados) e, depois, os objetos de exame.
    - Imagens são carregadas em lote (por ContentType do objeto concreto) e numeradas como
      Figuras contínuas (Figura 1, Figura 2, ...).
    """
    model = ReportCase
    template_name = "report_maker/reportcase_showpage.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        """
        Restringe a leitura ao autor do laudo e carrega relações úteis
        para evitar N+1 no template.
        """
        return (
            super()
            .get_queryset()
            .filter(author=self.request.user)
            .select_related("institution", "nucleus", "team", "author")
        )

    # ─────────────────────────────────────────────────────────────
    # Header builders
    # ─────────────────────────────────────────────────────────────
    def _build_header_from_user(self) -> dict:
        """
        Monta o cabeçalho institucional a partir do vínculo ATUAL do usuário.

        Usado apenas quando o laudo está editável (report.can_edit == True), pois o laudo
        ainda “acompanha” o contexto vigente do perito.
        """
        user = self.request.user

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

        if hon_title and hon_name:
            honoree_line = f"{hon_title} {hon_name}"
        else:
            honoree_line = hon_name or ""

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


    def _build_header_from_snapshots(self, report: ReportCase) -> dict:
        """
        Monta o cabeçalho institucional usando snapshots persistidos no ReportCase.

        Usado quando o laudo está concluído/bloqueado. Isso garante que:
        - o cabeçalho não muda se o usuário trocar de equipe/núcleo/instituição;
        - o documento mantém coerência histórica.
        """
        inst = report.institution  # fallback opcional só para emblemas

        name = (report.institution_name_snapshot or "").strip()
        acronym = (report.institution_acronym_snapshot or "").strip()
        kind_display = (report.institution_kind_snapshot or "").strip()

        hon_title = (report.honoree_title_snapshot or "").strip()
        hon_name = (report.honoree_name_snapshot or "").strip()

        if hon_title and hon_name:
            honoree_line = f"{hon_title} {hon_name}"
        else:
            honoree_line = hon_name or ""

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

    # ─────────────────────────────────────────────────────────────
    # Context
    # ─────────────────────────────────────────────────────────────
    def get_context_data(self, **kwargs):
        """
        Monta o context completo do laudo (cabeçalho + blocos + outline + figuras).

        O template espera:
        - header, preamble
        - outline (lista de grupos com objetos já enriquecidos com imagens + rótulos de figura)
        - numerações para Observações Finais e Conclusão (quando existirem)
        """
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # Header: regra combinada (atual x snapshot)
        can_edit = bool(getattr(report, "can_edit", False))
        header = self._build_header_from_user() if can_edit else self._build_header_from_snapshots(report)

        # Textos do laudo (inclui intros de grupo)
        text_blocks_qs = report.text_blocks.all().order_by("placement", "position", "created_at")
        ctx["text_blocks"] = text_blocks_qs

        by_placement = defaultdict(list)
        for tb in text_blocks_qs:
            by_placement[tb.placement].append(tb)
        ctx["text_blocks_by_placement"] = dict(by_placement)

        # Preâmbulo: usuário > sistema
        preamble_text = (
            text_blocks_qs
            .filter(placement=ReportTextBlock.Placement.PREAMBLE)
            .values_list("body", flat=True)
            .first()
        )
        preamble = (preamble_text or "").strip() or report.preamble

        # Objetos base (ordem do laudo) -> concretos via property .concrete
        base_objects = list(report.exam_objects.all().order_by("order", "created_at"))
        concrete_objects = [o.concrete for o in base_objects]

        # ─────────────────────────────────────────────
        # Blocos iniciais (ANTES do conteúdo) — ordem editorial fixa:
        # Resumo, Glossário, Sumário, Metadados (requisição/atendimento/objetivo etc.)
        # ─────────────────────────────────────────────
        meta_blocks = list(report.get_render_blocks() or [])
        prepend_blocks: list[dict] = []

        # Resumo
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

        # Glossário (se existir no enum; se não existir, ignora)
        glossary_placement = getattr(ReportTextBlock.Placement, "GLOSSARY", None)
        if glossary_placement:
            glossary_text = (
                text_blocks_qs
                .filter(placement=glossary_placement)
                .values_list("body", flat=True)
                .first()
            )
            if (glossary_text or "").strip():
                prepend_blocks.append({
                    "kind": "text_section",
                    "label": "Glossário",
                    "value": glossary_text,
                    "fmt": "md",
                })

        # Sumário (manual)
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

        # Metadados (requisição/atendimento/objetivo etc.) vêm depois
        prepend_blocks.extend(meta_blocks)

        # Outline principal
        outline, next_top = build_report_outline(
            report=report,
            exam_objects_qs=base_objects,
            text_blocks_qs=text_blocks_qs,
            start_at=1,
            prepend_blocks=prepend_blocks,
        )

        # Numeração de Observações Finais e Conclusão (se existirem)
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
            if not ct:
                continue
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
        # Monta outline "UI" com figuras contínuas
        # ─────────────────────────────────────────────
        figure_counter = 1
        outline_ui: list[dict] = []

        for g in outline:
            g_dict = asdict(g)
            g_objects_ui: list[dict] = []

            for o in g.objects:
                o_dict = asdict(o)
                obj = o.obj  # instância concreta (ou ReportCase no grupo virtual)

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

        # Context final
        ctx.update({
            "report_number": report.report_number,
            "header": header,
            "preamble": preamble,
            "outline": outline_ui,
            "next_top": next_top,
            "final_considerations_num": final_considerations_num,
            "final_considerations_blocks": final_considerations_blocks,
            "conclusion_num": conclusion_num,
            "conclusion_blocks": conclusion_blocks,
            "figure_counter_end": figure_counter,
        })

        return ctx
