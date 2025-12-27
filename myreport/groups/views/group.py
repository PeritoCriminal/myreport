# myreport/groups/views/group.py
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from ..forms import GroupForm
from ..models import Group, GroupMembership
from ..services import inactivate_group


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "groups/group_list.html"
    context_object_name = "groups"
    paginate_by = 20

    def get_queryset(self):
        q = (self.request.GET.get("q") or "").strip()

        qs = Group.objects.all().order_by("-created_at")

        if q:
            qs = qs.filter(Q(name__icontains=q))

        user = self.request.user

        qs = qs.annotate(
            is_creator=Case(
                When(creator_id=user.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            is_member=Exists(
                GroupMembership.objects.filter(
                    group_id=OuterRef("pk"),
                    user=user,
                )
            ),
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["group_create_url"] = reverse("groups:group_create")
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        return ctx


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = "groups/group_detail.html"
    context_object_name = "group"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if not obj.is_active and obj.creator_id != self.request.user.id:
            raise Http404("Grupo não encontrado.")
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        group = self.object
        user = self.request.user

        ctx["is_member"] = GroupMembership.objects.filter(group=group, user=user).exists()
        ctx["is_creator"] = group.creator_id == user.id

        qs_memberships = (
            group.memberships.select_related("user")
            .order_by("-joined_at")
        )

        ctx["members_count"] = qs_memberships.count()
        ctx["members"] = [m.user for m in qs_memberships]

        return ctx



class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "groups/group_form.html"
    success_url = reverse_lazy("groups:group_list")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)

        GroupMembership.objects.get_or_create(
            group=self.object,
            user=self.request.user,
        )
        return response


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "groups/group_form.html"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.creator_id != request.user.id:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("groups:group_detail", kwargs={"pk": self.object.pk})


@require_POST
def group_deactivate_view(request, pk):
    group = get_object_or_404(Group, pk=pk)
    try:
        inactivate_group(group=group, user=request.user)
    except PermissionDenied:
        raise Http404("Grupo não encontrado.")
    return redirect("groups:group_detail", pk=group.pk)

