from django.urls import path
from .views import HomeView, DashboardView


app_name = 'home'

urlpatterns = [
    path('', HomeView.as_view(), name='index'),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]