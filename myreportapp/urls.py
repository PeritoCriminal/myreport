from django.urls import path

from myreportapp.views import (
    home_view,
    image_editor_view,
    image_editor_view1,
    )

urlpatterns = [
    path('', home_view, name='home'),
    path('image_editor', image_editor_view, name='image_editor'),
    path('image_editor1', image_editor_view1, name='image_editor1'),
]
