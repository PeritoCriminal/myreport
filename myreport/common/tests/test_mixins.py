# common/mixins.py

from django import forms
from django.core.exceptions import PermissionDenied


class BootstrapFormMixin:
    """
    Aplica classes do Bootstrap 5 automaticamente aos widgets do form.

    Regras:
    - Input text / textarea / file -> form-control
    - Select / SelectMultiple -> form-select
    - CheckboxInput (único) -> form-check-input
    - RadioSelect / CheckboxSelectMultiple (listas) -> não força classes de input
    - HiddenInput -> ignorado
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    # -------------------------
    # Helpers de classe CSS
    # -------------------------

    def _get_classes(self, widget):
        return widget.attrs.get("class", "").split()

    def _set_classes(self, widget, classes):
        widget.attrs["class"] = " ".join(sorted(set(classes)))

    def _add_class(self, widget, class_name):
        classes = self._get_classes(widget)
        if class_name not in classes:
            classes.append(class_name)
            self._set_classes(widget, classes)

    def _remove_class(self, widget, class_name):
        classes = self._get_classes(widget)
        if class_name in classes:
            classes.remove(class_name)
            self._set_classes(widget, classes)

    # -------------------------
    # Bootstrap core
    # -------------------------

    def apply_bootstrap(self):
        for field in self.fields.values():
            self._apply_bootstrap_to_field(field)

    def _apply_bootstrap_to_field(self, field: forms.Field) -> None:
        widget = field.widget

        # hidden: não toca
        if getattr(widget, "input_type", None) == "hidden":
            return

        # checkbox único
        if isinstance(widget, forms.CheckboxInput):
            self._add_class(widget, "form-check-input")
            self._remove_class(widget, "form-control")
            self._remove_class(widget, "form-select")
            return

        # widgets que renderizam listas (não force classe de input)
        if isinstance(widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
            self._remove_class(widget, "form-control")
            self._remove_class(widget, "form-select")
            return

        # selects
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            self._add_class(widget, "form-select")
            self._remove_class(widget, "form-control")
            return

        # file
        if isinstance(widget, forms.ClearableFileInput):
            self._add_class(widget, "form-control")
            self._remove_class(widget, "form-select")
            return

        # default (text, textarea, number, email, etc)
        self._remove_class(widget, "form-select")
        self._add_class(widget, "form-control")

    # -------------------------
    # Erros
    # -------------------------

    def apply_error_classes(self) -> None:
        for name in self.errors.keys():
            if name not in self.fields:
                continue

            widget = self.fields[name].widget

            if getattr(widget, "input_type", None) == "hidden":
                continue

            self._add_class(widget, "is-invalid")

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            self.apply_error_classes()


class BaseForm(BootstrapFormMixin, forms.Form):
    """
    Base padrão para forms.Form no projeto (Bootstrap aplicado automaticamente).
    """
    pass


class BaseModelForm(BootstrapFormMixin, forms.ModelForm):
    """
    Base padrão para forms.ModelForm no projeto (Bootstrap aplicado automaticamente).
    """
    pass


class CanEditReportsRequiredMixin:
    """
    Exige que o usuário autenticado tenha a permissão efetiva
    de edição de laudos (can_edit_reports_effective).
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
    Injeta no contexto:
    - obj_app_label
    - obj_model_name

    Baseado no _meta do objeto principal da view.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = context.get("object")
        if obj and hasattr(obj, "_meta"):
            context["obj_app_label"] = obj._meta.app_label
            context["obj_model_name"] = obj._meta.model_name

        return context
