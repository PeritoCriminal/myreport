from django.urls import path

from myreportapp.views import (
    home_view,
    )

urlpatterns = [
    path('', home_view, name='home'),
]
