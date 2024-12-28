from django.urls import path

from myreportapp.views import (
    home_view,
    image_editor_view,
    )

urlpatterns = [
    path('', home_view, name='home'),
    path('image_editor', image_editor_view, name='image_editor'),
]
