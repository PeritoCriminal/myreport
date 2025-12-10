# accounts/urls.py
from django.urls import path
from .views import UserRegisterView, UserLoginView


app_name = 'accounts'

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(template_name="accounts/login.html"), name="login"),
]