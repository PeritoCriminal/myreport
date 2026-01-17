from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import SimpleTestCase, RequestFactory
from django.views import View

from common.mixins import (
    BootstrapFormMixin,
    CanEditReportsRequiredMixin,
    ExamObjectMetaContextMixin,
)


class DummyForm(BootstrapFormMixin, forms.Form):
    a = forms.CharField()
    b = forms.ChoiceField(choices=[("1", "1")])
    c = forms.CharField(widget=forms.Textarea)
    h = forms.CharField(widget=forms.HiddenInput)


class BootstrapFormMixinTests(SimpleTestCase):
    def test_applies_bootstrap_classes(self):
        form = DummyForm()

        # CharField / Textarea -> form-control
        self.assertIn("form-control", form.fields["a"].widget.attrs.get("class", ""))
        self.assertIn("form-control", form.fields["c"].widget.attrs.get("class", ""))

        # ChoiceField -> form-select
        self.assertIn("form-select", form.fields["b"].widget.attrs.get("class", ""))

        # HiddenInput não deve receber classes
        self.assertIsNone(form.fields["h"].widget.attrs.get("class"))


class CanEditReportsRequiredMixinTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_anonymous_user_uses_handle_no_permission(self):
        class V(CanEditReportsRequiredMixin, View):
            def handle_no_permission(self):
                return HttpResponse("nope", status=302)

            def get(self, request):
                return HttpResponse("ok")

        request = self.factory.get("/")
        request.user = AnonymousUser()

        response = V.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_without_permission_raises_403(self):
        class User:
            is_authenticated = True
            can_edit_reports_effective = False

        class V(CanEditReportsRequiredMixin, View):
            def handle_no_permission(self):
                return HttpResponse("nope", status=302)

            def get(self, request):
                return HttpResponse("ok")

        request = self.factory.get("/")
        request.user = User()

        with self.assertRaises(PermissionDenied):
            V.as_view()(request)


class ExamObjectMetaContextMixinTests(SimpleTestCase):
    def test_injects_app_and_model_into_context(self):
        class Obj:
            class _meta:
                app_label = "report_maker"
                model_name = "genericexamobject"

        class Base:
            def get_context_data(self, **kwargs):
                return {"object": Obj()}

        class V(ExamObjectMetaContextMixin, Base):
            pass

        view = V()
        context = view.get_context_data()

        self.assertEqual(context["obj_app_label"], "report_maker")
        self.assertEqual(context["obj_model_name"], "genericexamobject")
