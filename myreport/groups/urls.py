from django.urls import path

from .views.group import GroupCreateView, GroupDetailView, GroupListView, GroupUpdateView, group_inactivate_view
from .views.membership import group_join_view, group_leave_view

app_name = "groups"

urlpatterns = [
    path("", GroupListView.as_view(), name="group_list"),
    path("new/", GroupCreateView.as_view(), name="group_create"),
    path("<uuid:pk>/", GroupDetailView.as_view(), name="group_detail"),
    path("<uuid:pk>/edit/", GroupUpdateView.as_view(), name="group_update"),
    path("<uuid:pk>/join/", group_join_view, name="group_join"),
    path("<uuid:pk>/leave/", group_leave_view, name="group_leave"),
    path("<uuid:pk>/deactivate/", group_inactivate_view, name="group_deactivate"),
]
