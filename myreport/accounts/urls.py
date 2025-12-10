# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import UserRegisterView, UserLoginView, user_logout


app_name = 'accounts'

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", user_logout, name="logout"),
]