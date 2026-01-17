# <seu_app>/mixins.py
from __future__ import annotations

from django import forms
from django.core.exceptions import PermissionDenied


class BootstrapFormMixin:
    """
    Aplica automaticamente classes Bootstrap aos campos do formulário.

    Regras:
    - Inputs padrão / textarea / file -> form-control
    - Select / SelectMultiple -> form-select
    - Checkbox / radio -> form-check-input
    - Hidden -> ignora
    - Após validação: campos com erro recebem is-invalid
    """

    def _add_class(self, widget: forms.Widget, css: str) -> None:
        current = (widget.attrs.get("class") or "").strip()
        if not current:
            widget.attrs["class"] = css
            return
        parts = set(current.split())
        for item in css.split():
            parts.add(item)
        widget.attrs["class"] = " ".join(sorted(parts))

    def _remove_class(self, widget: forms.Widget, css: str) -> None:
        current = (widget.attrs.get("class") or "").strip()
        if not current:
            return
        parts = [c for c in current.split() if c != css]
        widget.attrs["class"] = " ".join(parts).strip()

    def _apply_bootstrap_to_field(self, field: forms.Field) -> None:
        widget = field.widget

        # hidden: não estiliza
        if getattr(widget, "input_type", None) == "hidden":
            return

        # checkbox / radio
        if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)):
            self._add_class(widget, "form-check-input")
            self._remove_class(widget, "form-control")
            self._remove_class(widget, "form-select")
            return

        # selects
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            self._add_class(widget, "form-select")
            self._remove_class(widget, "form-control")
            return

        # file input
        if isinstance(widget, forms.ClearableFileInput):
            self._add_class(widget, "form-control")
            return

        # textarea e inputs em geral
        self._add_class(widget, "form-control")

    def apply_bootstrap(self) -> None:
        for field in self.fields.values():
            self._apply_bootstrap_to_field(field)

    def apply_error_classes(self) -> None:
        """
        Marca campos com erro com a classe Bootstrap `is-invalid`.
        Deve rodar após o Django preencher `self.errors`.
        """
        for name in self.errors.keys():
            if name in self.fields:
                self._add_class(self.fields[name].widget, "is-invalid")


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

    Usado para URLs genéricas de objetos examináveis
    (imagens, anexos, etc.).
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context.get("obj") or context.get("object")
        if obj is not None:
            context["obj_app_label"] = obj._meta.app_label
            context["obj_model_name"] = obj._meta.model_name
        return context
