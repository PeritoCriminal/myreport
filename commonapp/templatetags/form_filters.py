# common/templatetags/form_filters.py


from django import template

register = template.Library()

@register.filter
def add_class(value, arg):
    """
    Adiciona uma classe CSS a um campo de formulário.
    Exemplo de uso: {{ form.field|add_class:"form-control" }}
    """
    return value.as_widget(attrs={'class': arg})
