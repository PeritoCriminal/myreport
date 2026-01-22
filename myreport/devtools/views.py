# devtools/views.py
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseServerError
from django.shortcuts import render

def error_403(request):
    raise PermissionDenied



def error_404(request):
    """
    Renderiza explicitamente o template 404.html.
    Útil para validar layout/tema independentemente do DEBUG.
    """
    response = render(request, "404.html", status=404)
    return response


def error_500(request):
    """
    Renderiza explicitamente o template 500.html.
    Útil para validar layout/tema independentemente do DEBUG.
    """
    return HttpResponseServerError(
        render(request, "500.html").content
    )