# common/mixins.py
from __future__ import annotations

from django import forms
from django.core.exceptions import PermissionDenied


class BootstrapFormMixin:
    """
    Padroniza widgets para Bootstrap 5 e marca campos inválidos automaticamente.

    Regras:
    - hidden: ignora
    - Select / SelectMultiple: form-select
    - CheckboxInput: form-check-input
    - RadioSelect / CheckboxSelectMultiple: container recebe classes úteis, sem forçar form-control
    - ClearableFileInput: form-control
    - demais: form-control
    - após validação (form bound): campos com erro recebem is-invalid
    """

    def _classes(self, widget: forms.Widget) -> set[str]:
        raw = (widget.attrs.get("class") or "").strip()
        return set(raw.split()) if raw else set()

    def _set_classes(self, widget: forms.Widget, classes: set[str]) -> None:
        widget.attrs["class"] = " ".join(sorted(c for c in classes if c)).strip() or ""

    def _add(self, widget: forms.Widget, *to_add: str) -> None:
        classes = self._classes(widget)
        for c in to_add:
            classes.update(c.split())
        self._set_classes(widget, classes)

    def _remove(self, widget: forms.Widget, *to_remove: str) -> None:
        classes = self._classes(widget)
        for c in to_remove:
            classes.discard(c)
        self._set_classes(widget, classes)

    def _is_hidden(self, widget: forms.Widget) -> bool:
        return getattr(widget, "input_type", None) == "hidden"

    def _apply_bootstrap_to_field(self, field: forms.Field) -> None:
        widget = field.widget

        if self._is_hidden(widget):
            return

        # Checkbox single
        if isinstance(widget, forms.CheckboxInput):
            self._remove(widget, "form-control", "form-select")
            self._add(widget, "form-check-input")
            return

        # Radio / Checkbox multiple
        if isinstance(widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
            # Não tenta enfiar form-control/form-select em widget que renderiza lista.
            # Mas mantém algo útil caso queira estilizar no template via CSS.
            self._remove(widget, "form-control", "form-select")
            self._add(widget, "form-check")  # classe no container
            return

        # Selects
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            self._remove(widget, "form-control")
            self._add(widget, "form-select")
            return

        # File
        if isinstance(widget, forms.ClearableFileInput):
            self._remove(widget, "form-select")
            self._add(widget, "form-control")
            return

        # Default
        self._remove(widget, "form-select")
        self._add(widget, "form-control")

    def apply_bootstrap(self) -> None:
        for field in self.fields.values():
            self._apply_bootstrap_to_field(field)

    def apply_error_classes(self) -> None:
        for name in self.errors.keys():
            if name in self.fields:
                widget = self.fields[name].widget
                if not self._is_hidden(widget):
                    self._add(widget, "is-invalid")


class BaseForm(BootstrapFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            self.apply_error_classes()


class BaseModelForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            self.apply_error_classes()


class CanEditReportsRequiredMixin:
    """
    Restringe acesso a views de criação/edição de laudos.

    Exige:
    - usuário autenticado;
    - habilitação administrativa;
    - vínculo institucional ativo.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return self.handle_no_permission()

        if not getattr(user, "can_edit_reports_effective", False):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class ExamObjectMetaContextMixin:
    """
    Adiciona ao contexto do template:
    - obj_app_label
    - obj_model_name
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context.get("obj") or context.get("object")
        if obj is not None:
            context["obj_app_label"] = obj._meta.app_label
            context["obj_model_name"] = obj._meta.model_name
        return context
