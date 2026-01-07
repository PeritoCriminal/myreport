class BootstrapFormMixin:
    """
    Aplica automaticamente classes Bootstrap aos campos do formulário.

    Regras:
    - Inputs padrão -> form-control
    - Textarea -> form-control
    - Select -> form-select
    - Campos hidden são ignorados
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            widget = field.widget

            # Ignora campos ocultos
            if getattr(widget, "input_type", None) == "hidden":
                continue

            classes = widget.attrs.get("class", "").strip()

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
