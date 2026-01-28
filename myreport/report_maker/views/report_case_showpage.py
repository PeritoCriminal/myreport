# myreport/report_maker/views/report_case_showpage.py

from __future__ import annotations

from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.views.generic import DetailView

from report_maker.models import ReportCase
from report_maker.models.images import ObjectImage


class ReportCaseShowPageView(LoginRequiredMixin, DetailView):
    """
    Página de visualização/preview do laudo (A4), com:
    - cabeçalho institucional (se can_edit: dados do usuário; senão: snapshots)
    - preâmbulo
    - Dados do Boletim (T1)
    - Dados da Requisição (T1)
    - Objetos de exame (cada obj = T1, campos = T2)
    - Figuras com numeração contínua (Figura 1..N)
    """
    model = ReportCase
    template_name = "report_maker/report_case_showpage.html"
    context_object_name = "report"
    pk_url_kwarg = "pk"

    # ─────────────────────────────────────────────────────────────
    # Queryset guard
    # ─────────────────────────────────────────────────────────────
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(author=self.request.user)
            .select_related("institution", "nucleus", "team", "author")
        )

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def _kv(self, label: str, value) -> dict:
        return {"label": label, "value": "" if value is None else value}

    def _get_concrete_obj(self, obj):
        """
        Resolve o objeto concreto (multi-table inheritance).
        Ajuste a lista conforme você adicionar novos tipos.
        """
        for rel in (
            "publicroadexamobject",
            "genericexamobject",
            # "vehicleexamobject",
            # "corpseexamobject",
        ):
            child = getattr(obj, rel, None)
            if child is not None:
                return child
        return obj

    def _build_bo_fields(self, report: ReportCase) -> list[dict]:
        return [
            self._kv("Boletim de ocorrência", report.police_report),
            self._kv("Inquérito policial", report.police_inquiry),
            self._kv("Distrito policial", report.police_station),
            self._kv("Tipificação penal", report.criminal_typification),
            self._kv("Data e hora da ocorrência", report.occurrence_datetime),
            self._kv("Data e hora da designação", report.assignment_datetime),
            self._kv("Data e hora do exame pericial", report.examination_datetime),
        ]

    def _build_req_fields(self, report: ReportCase) -> list[dict]:
        return [
            self._kv("Autoridade requisitante", report.requesting_authority),
            self._kv("Objetivo", report.get_objective_display() if report.objective else ""),
            self._kv("Protocolo", report.protocol),
            self._kv("Fotografia", report.photography_by),
            self._kv("Croqui", report.sketch_by),
        ]

    def _build_obj_field_groups(self, obj) -> list[dict]:
        """
        Extrai campos "textuais" do model concreto para exibição como T2.

        Observação:
        - Isso varre _meta.fields e ignora IDs, relações e metadados.
        - Se quiser controle total por tipo de objeto, depois trocamos por
          uma lista explícita por model.
        """
        skip_names = {
            "id", "pk",
            "report_case",
            "order", "created_at", "updated_at",
            "status", "is_locked",
            "is_active",
        }

        out = []
        for f in obj._meta.fields:
            if f.name in skip_names:
                continue
            if f.is_relation:
                continue

            value = getattr(obj, f.name, "")
            if value in (None, ""):
                continue

            out.append({
                "label": str(getattr(f, "verbose_name", f.name)).capitalize(),
                "value": value,
            })
        return out

    # ─────────────────────────────────────────────────────────────
    # Header builders (VIEW-driven, conforme combinado)
    # ─────────────────────────────────────────────────────────────
    def _build_header_from_user(self) -> dict:
        """
        Se can_edit: busca dados a partir dos vínculos ativos do usuário logado.
        """
        user = self.request.user

        aia = getattr(user, "active_institution_assignment", None)
        inst = getattr(aia, "institution", None)

        ata = getattr(user, "active_team_assignment", None)
        team = getattr(ata, "team", None)
        nucleus = getattr(team, "nucleus", None) if team else None

        name = (getattr(inst, "name", "") or "") if inst else ""
        acronym = (getattr(inst, "acronym", "") or "") if inst else ""

        if inst and hasattr(inst, "get_kind_display"):
            kind_display = inst.get_kind_display()
        else:
            kind_display = str(getattr(inst, "kind", "") or "") if inst else ""

        hon_title = (getattr(inst, "honoree_title", "") or "") if inst else ""
        hon_name = (getattr(inst, "honoree_name", "") or "") if inst else ""

        honoree_line = ""
        if hon_title and hon_name:
            honoree_line = f"{hon_title} {hon_name}"
        elif hon_name:
            honoree_line = hon_name

        unit_line = " - ".join(p for p in [
            (getattr(nucleus, "name", "") or "") if nucleus else "",
            (getattr(team, "name", "") or "") if team else "",
        ] if p)

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
        Se não can_edit: busca estritamente dos snapshots do laudo.
        """
        inst = report.institution  # fallback opcional só para emblemas (se existir FK)

        name = (report.institution_name_snapshot or "").strip()
        acronym = (report.institution_acronym_snapshot or "").strip()
        kind_display = (report.institution_kind_snapshot or "").strip()

        hon_title = (report.honoree_title_snapshot or "").strip()
        hon_name = (report.honoree_name_snapshot or "").strip()

        honoree_line = ""
        if hon_title and hon_name:
            honoree_line = f"{hon_title} {hon_name}"
        elif hon_name:
            honoree_line = hon_name

        unit_line = " - ".join(p for p in [report.nucleus_display, report.team_display] if p)

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
        ctx = super().get_context_data(**kwargs)
        report: ReportCase = ctx["report"]

        # ─────────────────────────────────────────────
        # Header: regra combinada
        # ─────────────────────────────────────────────
        can_edit = bool(getattr(report, "can_edit", False))
        header = self._build_header_from_user() if can_edit else self._build_header_from_snapshots(report)

        # ─────────────────────────────────────────────
        # Numeração T1/T2 (como você definiu)
        # ─────────────────────────────────────────────
        T1 = 1

        def next_t1() -> int:
            nonlocal T1
            n = T1
            T1 += 1
            return n

        def build_t2_groups(obj, t1_number: int) -> list[dict]:
            T2 = 1
            groups = []
            for fg in self._build_obj_field_groups(obj):
                groups.append({
                    **fg,
                    "t2": f"{t1_number}.{T2}",
                })
                T2 += 1
            return groups

        # ─────────────────────────────────────────────
        # Seções fixas (T1)
        # ─────────────────────────────────────────────
        section_nums = {
            "bo": next_t1(),   # 1
            "req": next_t1(),  # 2
        }

        # ─────────────────────────────────────────────
        # Objetos (base -> concreto) preservando ordem
        # ─────────────────────────────────────────────
        base_objects = list(
            report.exam_objects.all()
            .order_by("order", "created_at")
        )
        concrete_objects = [self._get_concrete_obj(o) for o in base_objects]

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
        # Monta UI final: T1/T2 + Figuras contínuas
        # ─────────────────────────────────────────────
        figure_counter = 1
        exam_objects_ui = []

        for obj in concrete_objects:
            ct = ct_map.get(obj.__class__)
            ct_id = ct.id if ct else None

            t1_num = next_t1()  # 3, 4, 5...

            images_ui = []
            for img in images_by_key.get((ct_id, obj.pk), []):
                images_ui.append({
                    "img": img,
                    "figure_label": f"Figura {figure_counter}",
                })
                figure_counter += 1

            exam_objects_ui.append({
                "obj": obj,
                "t1": t1_num,
                "title": getattr(obj, "title", "") or "Objeto sem título",
                "field_groups": build_t2_groups(obj, t1_num),
                "images": images_ui,
            })

        ctx.update({
            "report_number": report.report_number,
            "header": header,
            "preamble": report.preamble,
            "bo_fields": self._build_bo_fields(report),
            "req_fields": self._build_req_fields(report),
            "section_nums": section_nums,
            "exam_objects_ui": exam_objects_ui,
        })
        return ctx
