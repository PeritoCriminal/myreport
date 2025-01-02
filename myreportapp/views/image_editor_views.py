

from django.shortcuts import render


def image_editor_view(request):
    return render(request, 'image_editor.html')


def image_editor_view1(request):
    return render(request, 'image_editor1.html')