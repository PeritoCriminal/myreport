

from django.shortcuts import render


def image_editor_view(request):
    return render(request, 'image_editor.html')