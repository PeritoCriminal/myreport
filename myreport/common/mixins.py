# <seu_app>/mixins.py
from __future__ import annotations

from django import forms
from django.core.exceptions import PermissionDenied


class BootstrapFormMixin:
    """
    Aplica automaticamente classes Bootstrap aos campos do formulário.

    Regras:
    - Inputs padrão -> form-control
    - Textarea -> form-control
    - Select -> form-select
    - Campos hidden são ignorados

    Observação:
    - Não executa nada sozinho no __init__. Use via BaseForm/BaseModelForm
      (ou chame apply_bootstrap() manualmente).
    """

    def apply_bootstrap(self) -> None:
        for field in self.fields.values():
            widget = field.widget

            # Ignora campos ocultos
            if getattr(widget, "input_type", None) == "hidden":
                continue

            classes = (widget.attrs.get("class") or "").strip()

            # Select
            if widget.__class__.__name__ in ("Select", "SelectMultiple"):
                widget.attrs["class"] = f"{classes} form-select".strip()
                continue

            # Textarea
            if widget.__class__.__name__ == "Textarea":
                widget.attrs["class"] = f"{classes} form-control".strip()
                continue

            # Inputs padrão
            widget.attrs["class"] = f"{classes} form-control".strip()


class BaseForm(BootstrapFormMixin, forms.Form):
    """
    Base para forms.Form com Bootstrap automático.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class BaseModelForm(BootstrapFormMixin, forms.ModelForm):
    """
    Base para forms.ModelForm com Bootstrap automático.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


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
