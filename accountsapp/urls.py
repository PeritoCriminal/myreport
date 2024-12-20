# accountsapp/urls.py

from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from accountsapp.views import (
    user_view,
    user_registration_view,
    confirmation_email_view,
    verify_email,
    complete_registration_view,
    )

urlpatterns = [
    path('profile/', user_view, name='user'),
    path('register/', user_registration_view, name='register'),
    path('verify-email/<uidb64>/<token>/', verify_email, name='verify_email'),
    path('confirmation-email/', confirmation_email_view, name='confirmation_email'),
    path('login/', LoginView.as_view(template_name='user_login.html'), name='login'),
    path('complete_registration/<int:id>', complete_registration_view, name='complete_registration'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

