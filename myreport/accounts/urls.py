# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    UserPreferencesUpdateView,
    UserRegisterView, 
    UserLoginView, 
    user_logout, 
    UserProfileUpdateView, 
    UserPasswordChangeView,
    AllUserListView,
    UserProfileView,
    FollowToggleView,
    LinkInstitutionView,
    ajax_nuclei,
    ajax_teams,
)

app_name = 'accounts'

urlpatterns = [
    path("preferences/", UserPreferencesUpdateView.as_view(), name="preferences",),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("profile/edit/", UserProfileUpdateView.as_view(), name="profile_edit"),
    path("password/change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("login/", UserLoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", user_logout, name="logout"),
    path("users/", AllUserListView.as_view(), name="user_list"),
    path("u/<uuid:user_id>/", UserProfileView.as_view(), name="user_profile"),
    path("u/<uuid:user_id>/follow-toggle/", FollowToggleView.as_view(), name="follow_toggle"),
    path("vinculo/", LinkInstitutionView.as_view(), name="link_institution"),

    # AJAX
    path("ajax/nuclei/", ajax_nuclei, name="ajax_nuclei"),
    path("ajax/teams/", ajax_teams, name="ajax_teams"),
]