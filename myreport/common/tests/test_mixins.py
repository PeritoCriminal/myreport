# common/tests/test_mixins.py

from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import SimpleTestCase, RequestFactory
from django.views import View

from common.form_mixins import BootstrapFormMixin, CanEditReportsRequiredMixin, ExamObjectMetaContextMixin


class DummyForm(BootstrapFormMixin, forms.Form):
    a = forms.CharField()
    b = forms.ChoiceField(choices=[("1", "1")])
    c = forms.CharField(widget=forms.Textarea)
    h = forms.CharField(widget=forms.HiddenInput)


class BootstrapFormMixinTests(SimpleTestCase):
    def test_applies_bootstrap_classes(self):
        f = DummyForm()
        self.assertIn("form-control", f.fields["a"].widget.attrs.get("class", ""))
        self.assertIn("form-select", f.fields["b"].widget.attrs.get("class", ""))
        self.assertIn("form-control", f.fields["c"].widget.attrs.get("class", ""))
        # hidden ignorado
        self.assertEqual(f.fields["h"].widget.attrs.get("class"), None)


class _ViewForCanEdit(LoginRequiredMixin := object):  # só para não importar LoginRequiredMixin aqui
    pass


class CanEditReportsRequiredMixinTests(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_anonymous_uses_handle_no_permission(self):
        class V(CanEditReportsRequiredMixin, View):
            def handle_no_permission(self):
                return HttpResponse("nope", status=302)

            def get(self, request):
                return HttpResponse("ok")

        req = self.rf.get("/")
        req.user = AnonymousUser()
        resp = V.as_view()(req)
        self.assertEqual(resp.status_code, 302)

    def test_logged_without_effective_permission_raises_403(self):
        class User:
            is_authenticated = True
            can_edit_reports_effective = False

        class V(CanEditReportsRequiredMixin, View):
            def handle_no_permission(self):
                return HttpResponse("nope", status=302)

            def get(self, request):
                return HttpResponse("ok")

        req = self.rf.get("/")
        req.user = User()
        with self.assertRaises(PermissionDenied):
            V.as_view()(req)


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

        v = V()
        ctx = v.get_context_data()
        self.assertEqual(ctx["obj_app_label"], "report_maker")
        self.assertEqual(ctx["obj_model_name"], "genericexamobject")

