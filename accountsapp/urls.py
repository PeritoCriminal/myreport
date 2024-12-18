

from django.urls import path
from django.contrib.auth.views import LogoutView

from accountsapp.views import (
    user_view,
    user_registration_view,
    verify_email,
    # confirm_registration_view,
    # complete_registration_view,
    )

urlpatterns = [
    path('profile/', user_view, name='user'),
    path('register/', user_registration_view, name='register'),
    path('verify-email/<uidb64>/<token>/', verify_email, name='verify_email'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # path('confirm/<uidb64>/<token>/', confirm_registration_view, name='confirm_registration'),
    # path('complete-registration/', complete_registration_view, name='complete_registration'),

]
