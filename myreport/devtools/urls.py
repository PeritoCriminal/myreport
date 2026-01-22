# devtools/urls.py

from django.urls import path
from . import views

app_name = "devtools"

urlpatterns = [
    path("403/", views.error_403, name="error_403"),
    path("404/", views.error_404, name="error_404"),
    path("500/", views.error_500, name="error_500"),
]
