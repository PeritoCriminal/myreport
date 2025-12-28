from django.urls import path
from .views import IndexView, DashboardView


app_name = 'home'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]