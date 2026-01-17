from __future__ import annotations

from django import forms
from django.core.exceptions import PermissionDenied
from django.views.generic.base import ContextMixin


class BaseForm:
    """
    Aplica automaticamente classes Bootstrap aos widgets do form.

    Regras:
    - TextInput, EmailInput, NumberInput, Textarea, FileInput, Date/DateTimeInput → form-control
    - Select / SelectMultiple → form-select
    - HiddenInput, Checkbox, Radio, widgets de lista → ignorados
    """

    CONTROL_WIDGETS = (
        forms.TextInput,
        forms.EmailInput,
        forms.NumberInput,
        forms.URLInput,
        forms.PasswordInput,
        forms.Textarea,
        forms.FileInput,
        forms.ClearableFileInput,
        forms.DateInput,
        forms.DateTimeInput,
        forms.TimeInput,
    )

    SELECT_WIDGETS = (
        forms.Select,
        forms.SelectMultiple,
    )

    IGNORE_WIDGETS = (
        forms.HiddenInput,
        forms.CheckboxInput,
        forms.RadioSelect,
        forms.CheckboxSelectMultiple,
    )

    def apply_bootstrap(self) -> None:
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, self.IGNORE_WIDGETS):
                continue

            if isinstance(widget, self.SELECT_WIDGETS):
                self._remove_class(widget, "form-control")
                self._add_class(widget, "form-select")
                continue

            if isinstance(widget, self.CONTROL_WIDGETS):
                self._remove_class(widget, "form-select")
                self._add_class(widget, "form-control")

    @staticmethod
    def _add_class(widget: forms.Widget, css_class: str) -> None:
        classes = (widget.attrs.get("class") or "").split()
        if css_class not in classes:
            classes.append(css_class)
        widget.attrs["class"] = " ".join(classes)

    @staticmethod
    def _remove_class(widget: forms.Widget, css_class: str) -> None:
        classes = (widget.attrs.get("class") or "").split()
        classes = [c for c in classes if c != css_class]
        if classes:
            widget.attrs["class"] = " ".join(classes)
        else:
            widget.attrs.pop("class", None)


class BaseModelForm(BaseForm, forms.ModelForm):
    """
    Base para todos os ModelForms do projeto.

    - Aplica Bootstrap automaticamente no __init__
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class CanEditReportsRequiredMixin:
    """
    Mixin de permissão:
    exige user autenticado com can_edit_reports_effective = True
    """

    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return self.handle_no_permission()

        if not getattr(user, "can_edit_reports_effective", False):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class ExamObjectMetaContextMixin(ContextMixin):
    """
    Injeta no contexto:
    - obj_app_label
    - obj_model_name

    Usado para GenericForeignKey e templates genéricos.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = context.get("object")
        if obj and hasattr(obj, "_meta"):
            context["obj_app_label"] = obj._meta.app_label
            context["obj_model_name"] = obj._meta.model_name

        return context
