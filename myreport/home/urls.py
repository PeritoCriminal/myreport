from django.urls import path
from .views import IndexView, DashboardView, ZenDoLaudoView


app_name = 'home'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("zen-do-laudo/", ZenDoLaudoView.as_view(), name="zen_do_laudo"),
]