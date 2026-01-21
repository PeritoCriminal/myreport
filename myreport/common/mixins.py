# myreport/common/mixins.py

from __future__ import annotations

from django import forms
from django.core.exceptions import PermissionDenied
from django.views.generic.base import ContextMixin
from django.http import Http404

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
    """
    Base padrão para forms.ModelForm no projeto.

    Padrão para campos renderizados via partial `text_block_editor.html`:
    - garante widget Textarea (aceita quebra de linha)
    - permite definir rows por campo (opcional)
    """

    TEXT_BLOCK_FIELDS: tuple[str, ...] = ()
    TEXT_BLOCK_ROWS: dict[str, int] = {}
    TEXT_BLOCK_DEFAULT_ROWS: int = 8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_text_block_widgets()

        # como o BootstrapFormMixin já aplicou classes no __init__,
        # reaplica para garantir que o widget final (Textarea) esteja com classes corretas
        self.apply_bootstrap()

    def apply_text_block_widgets(self) -> None:
        for name in getattr(self, "TEXT_BLOCK_FIELDS", ()):
            if name not in self.fields:
                continue

            field = self.fields[name]

            # garante multiline (quebra de linha)
            if not isinstance(field.widget, forms.Textarea):
                field.widget = forms.Textarea()

            # rows (opcional; o partial também pode controlar visualmente)
            rows = (getattr(self, "TEXT_BLOCK_ROWS", {}) or {}).get(name, self.TEXT_BLOCK_DEFAULT_ROWS)
            field.widget.attrs.setdefault("rows", rows)


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


class ExamObjectMetaContextMixin:
    """
    Injeta metadados do objeto principal no context:
    - obj_app_label
    - obj_model_name

    Funciona tanto para CBVs que usam self.object (Detail/Update)
    quanto para views que já colocam 'object' ou outro nome no context.
    """

    obj_context_name = "object"  # pode sobrescrever na view, se usar outro nome

    def _get_context_object(self, context):
        # 1) padrão de SingleObjectMixin
        obj = getattr(self, "object", None)
        if obj is not None:
            return obj

        # 2) padrão 'object' no context
        obj = context.get("object")
        if obj is not None:
            return obj

        # 3) se a view usa context_object_name customizado
        name = getattr(self, "context_object_name", None)
        if name and context.get(name) is not None:
            return context.get(name)

        # 4) fallback explícito do mixin
        name = getattr(self, "obj_context_name", "object")
        return context.get(name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = self._get_context_object(context)
        if obj is not None and hasattr(obj, "_meta"):
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
    



def owner_id(owner):
    """
    Suporta owner ser:
    - um User (owner.id)
    - um inteiro (snapshot ou FK desnormalizada)
    """
    return getattr(owner, "id", owner)


class OwnerOr404Mixin:
    """
    Garante que apenas o dono do objeto possa acessá-lo.
    Caso contrário, retorna 404 para não vazar a existência do objeto.
    """

    owner_field = "user"  # ajuste se o model usar outro nome

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        owner = getattr(obj, self.owner_field, None)

        if owner is None or owner_id(owner) != self.request.user.id:
            raise Http404

        return obj


class EditNotOpenedByThirdPartyOr404Mixin:
    """
    Bloqueia edição/exclusão quando a regra de negócio impedir
    (ex.: postagem já aberta por terceiros).
    Retorna 404 para manter consistência e evitar vazamento.
    """

    opened_flag_field = "opened_by_third_party"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if getattr(obj, self.opened_flag_field, False):
            raise Http404

        return super().dispatch(request, *args, **kwargs)



class ProfileImageContextMixin:
    """
    Injeta `profile_image` no contexto, seguro para uso de `.url` no template.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = getattr(self.request, "user", None)
        img = getattr(user, "profile_image", None) if user and user.is_authenticated else None

        # img pode existir como FieldFile, mas sem arquivo associado
        context["profile_image"] = img if getattr(img, "name", "") else None
        return context