from __future__ import annotations

from django import forms
from django.core.exceptions import PermissionDenied
from django.views.generic.base import ContextMixin

from django.http import HttpResponseRedirect

from django.shortcuts import redirect


class BootstrapFormMixin:
    """
    Aplica automaticamente classes Bootstrap aos widgets do form.

    Regras:
    - TextInput, EmailInput, NumberInput, Textarea, FileInput, Date/DateTimeInput -> form-control
    - Select / SelectMultiple -> form-select
    - HiddenInput, Checkbox, RadioSelect, CheckboxSelectMultiple -> ignorados
    - Campos com erro (form bound) -> is-invalid
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

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

    def apply_error_classes(self) -> None:
        for name in self.errors.keys():
            if name not in self.fields:
                continue
            widget = self.fields[name].widget
            if isinstance(widget, forms.HiddenInput):
                continue
            self._add_class(widget, "is-invalid")

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

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            self.apply_error_classes()


class BaseForm(BootstrapFormMixin, forms.Form):
    """Base padrão para forms.Form no projeto."""
    pass


class BaseModelForm(BootstrapFormMixin, forms.ModelForm):
    """Base padrão para forms.ModelForm no projeto."""
    pass


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
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = context.get("object")
        if obj and hasattr(obj, "_meta"):
            context["obj_app_label"] = obj._meta.app_label
            context["obj_model_name"] = obj._meta.model_name

        return context
    


# ─────────────────────────────────────────
# VIEW MIXINS (CBVs)
# ─────────────────────────────────────────



class BootstrapFormViewMixin:
    """
    Injeta automaticamente um mixin base de Bootstrap no form da view.

    Uso:
        class MinhaView(BootstrapFormViewMixin, CreateView):
            form_base_class = BootstrapFormMixin
    """

    form_base_class = None

    def get_form_class(self):
        form_class = super().get_form_class()

        if self.form_base_class and self.form_base_class not in form_class.__mro__:
            class WrappedForm(self.form_base_class, form_class):
                pass

            return WrappedForm

        return form_class


class OwnerRequiredMixin:
    """
    Restringe acesso à view apenas ao proprietário do objeto.
    """

    owner_field = "user"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        owner = getattr(obj, self.owner_field, None)

        if owner != request.user:
            raise PermissionDenied("Acesso restrito ao proprietário do registro.")

        return super().dispatch(request, *args, **kwargs)


class ActiveObjectRequiredMixin:
    """
    Impede ações sobre objetos marcados como inativos.
    """

    active_field = "is_active"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if hasattr(obj, self.active_field) and not getattr(obj, self.active_field):
            raise PermissionDenied("Este registro encontra-se inativo.")

        return super().dispatch(request, *args, **kwargs)


class UserAssignMixin:
    """
    Atribui automaticamente o usuário logado ao salvar o form.
    """

    user_field = "user"

    def form_valid(self, form):
        if not getattr(form.instance, self.user_field, None):
            setattr(form.instance, self.user_field, self.request.user)

        return super().form_valid(form)


class SoftDeleteMixin:
    """
    Substitui a exclusão física por desativação lógica.
    """

    active_field = "is_active"

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        setattr(obj, self.active_field, False)
        obj.save()
        return HttpResponseRedirect(self.get_success_url())


class ContextTitleMixin:
    """
    Padroniza títulos e subtítulos no contexto do template.
    """

    page_title = None
    page_subtitle = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.page_title:
            context["page_title"] = self.page_title
        if self.page_subtitle:
            context["page_subtitle"] = self.page_subtitle

        return context

# ─────────────────────────────────────────
# BLOCKING MIXINS
# ─────────────────────────────────────────

class BlockIfOpenedByThirdPartyMixin:
    """
    Bloqueia ações (Update/Delete) se o objeto já foi aberto por terceiro.

    Útil para regras de imutabilidade após visualização externa.
    """

    block_field = "opened_by_third_party"
    redirect_url_name = None  # ex: "social_net:post_list"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # garante que self.object já existe
        if getattr(self.object, self.block_field, False):
            if self.redirect_url_name:
                return redirect(self.redirect_url_name)

            raise PermissionDenied("Este registro não pode mais ser alterado.")

        return response

