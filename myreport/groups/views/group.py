# myreport/groups/views/group.py
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Value, When, Prefetch, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.core.paginator import Paginator

from ..forms import GroupForm
from ..models import Group, GroupMembership
from ..services import inactivate_group

from social_net.models import Post, PostComment, PostLike, PostRating
from social_net.forms import PostForm


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
        ).order_by(
            Case(
                When(is_member=True, then=Value(0)),  # primeiro grupos que participa
                default=Value(1),
                output_field=BooleanField(),
            ),
            "name",  # depois, ordem alfabética
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

        ctx["is_member"] = GroupMembership.objects.filter(
            group=group,
            user=user,
        ).exists()

        ctx["is_creator"] = group.creator_id == user.id

        qs_memberships = (
            group.memberships
            .select_related("user")
            .order_by("-joined_at")
        )

        ctx["members_count"] = qs_memberships.count()
        ctx["members"] = [m.user for m in qs_memberships]

        # NOVO: publicações do grupo
        qs_posts = (
            Post.objects
            .filter(is_active=True, group=group)
            .select_related("user")
            .order_by("-created_at")
        )

        ctx["posts"] = qs_posts
        ctx["posts_count"] = qs_posts.count()

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




class GroupFeedView(LoginRequiredMixin, DetailView):
    """
    Feed exclusivo de um grupo.

    Exibe apenas postagens ativas vinculadas ao grupo,
    permitindo criação de novas postagens já pré-selecionadas no grupo.
    """

    model = Group
    template_name = "groups/group_feed.html"
    context_object_name = "group"

    def dispatch(self, request, *args, **kwargs):
        # carrega o grupo (DetailView usa pk por padrão)
        self.object = self.get_object()

        # 1) Grupo inativo e usuário não é criador → vai para detail
        if not self.object.is_active and self.object.creator_id != request.user.id:
            return redirect("groups:group_detail", pk=self.object.pk)

        # 2) Usuário não é membro nem criador → vai para detail
        is_member = GroupMembership.objects.filter(
            group=self.object,
            user=request.user,
        ).exists()

        if not is_member and self.object.creator_id != request.user.id:
            return redirect("groups:group_detail", pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        group = self.object
        user = self.request.user

        # Comentários (nível raiz)
        comments_qs = (
            PostComment.objects
            .filter(is_active=True, parent__isnull=True)
            .select_related("user")
            .order_by("-created_at")
        )

        # Subquery: nota do usuário logado
        user_rating_value_sq = (
            PostRating.objects
            .filter(post_id=OuterRef("pk"), user_id=user.pk)
            .values("value")[:1]
        )

        # Feed do grupo
        qs = (
            Post.objects
            .filter(is_active=True, group=group)
            .select_related("user", "group")
            .annotate(
                has_liked=Exists(
                    PostLike.objects.filter(
                        post_id=OuterRef("pk"),
                        user_id=user.pk,
                    )
                ),
                has_rated=Exists(
                    PostRating.objects.filter(
                        post_id=OuterRef("pk"),
                        user_id=user.pk,
                    )
                ),
                user_rating_value=Subquery(user_rating_value_sq),
            )
            .prefetch_related(Prefetch("comments", queryset=comments_qs))
            .order_by("-updated_at")
        )

        # Busca
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(title__icontains=q)

        # Paginação
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        ctx["posts"] = page_obj
        ctx["page_obj"] = page_obj
        ctx["is_paginated"] = page_obj.has_other_pages()

        # Form de postagem já apontando para o grupo
        ctx["form"] = PostForm(
            user=user,
            initial={"group": group},
        )

        ctx["rating_range"] = range(1, 6)
        ctx["stars_5"] = range(1, 6)

        # Últimos comentários (feed)
        for post in ctx["posts"]:
            post.last_comments = list(post.comments.all())[:5]

        return ctx

