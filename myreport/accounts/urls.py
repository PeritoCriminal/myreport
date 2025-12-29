# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    UserRegisterView, 
    UserLoginView, 
    user_logout, 
    UserProfileUpdateView, 
    UserPasswordChangeView,
    AllUserListView,
    UserProfileView,
    FollowToggleView,
)

app_name = 'accounts'

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("profile/edit/", UserProfileUpdateView.as_view(), name="profile_edit"),
    path("password/change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("login/", UserLoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", user_logout, name="logout"),
    path("users/", AllUserListView.as_view(), name="user_list"),
    path("u/<uuid:user_id>/", UserProfileView.as_view(), name="user_profile"),
    path("u/<uuid:user_id>/follow-toggle/", FollowToggleView.as_view(), name="follow_toggle"),
]