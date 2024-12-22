

from django.shortcuts import render


def teste_view(request):
    return render(request, 'teste.html')