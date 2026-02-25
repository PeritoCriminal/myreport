# report_maker/tests/test_views_ai.py
from __future__ import annotations

import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


UserModel = get_user_model()


class AITexblockGenerateViewTests(TestCase):
    """
    Testes da view report_maker.views.ai_textblock.ai_textblock_generate

    Objetivos:
    - Garantir contrato HTTP (login_required + require_POST).
    - Validar payload mínimo.
    - Validar sucesso (retorno {"text": ...}).
    - Validar tratamento de erros de API (429/401/503) sem chamar a OpenAI real.

    Observação:
    - O nome da URL pode variar no seu projeto; este arquivo tenta algumas opções.
      Se falhar, ajuste AI_URL_NAMES abaixo.
    """

    AI_URL_NAMES = (
        "report_maker:ai_textblock_generate",
        "report_maker:ai_text_block_generate",
        "report_maker:ai_generate_textblock",
    )

    def setUp(self):
        self.user = UserModel.objects.create_user(username="u1", password="pass123")

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
    def login(self):
        ok = self.client.login(username=self.user.username, password="pass123")
        self.assertTrue(ok)

    def ai_url(self) -> str:
        errors = []
        for name in self.AI_URL_NAMES:
            try:
                return reverse(name)
            except NoReverseMatch as e:
                errors.append(f"{name}: {e}")
        raise AssertionError(
            "Não foi possível resolver a URL da view de IA. Ajuste AI_URL_NAMES.\n"
            + "\n".join(errors)
        )

    def post_json(self, url: str, payload: dict):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    # ─────────────────────────────────────────────
    # Contrato básico
    # ─────────────────────────────────────────────
    def test_get_not_allowed(self):
        # require_POST => 405
        self.login()
        resp = self.client.get(self.ai_url())
        self.assertEqual(resp.status_code, 405)

    def test_post_requires_login(self):
        # login_required => 302
        resp = self.post_json(self.ai_url(), {"kind": "generic", "notes": "abc"})
        self.assertEqual(resp.status_code, 302)

    def test_post_requires_notes(self):
        self.login()
        resp = self.post_json(self.ai_url(), {"kind": "generic", "notes": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text", resp.json())
        self.assertTrue(resp.json()["text"].strip())
        self.assertJSONEqual(resp.content, {"error": "notes_required"})

    # ─────────────────────────────────────────────
    # Sucesso (mock do OpenAI)
    # ─────────────────────────────────────────────
    @patch("report_maker.views.ai_textblock.OpenAI")
    def test_success_returns_text(self, OpenAIMock: Mock):
        self.login()

        # Simula resp.output_text
        fake_resp = Mock()
        fake_resp.output_text = "TEXTO GERADO"

        client_instance = Mock()
        client_instance.responses.create.return_value = fake_resp
        OpenAIMock.return_value = client_instance

        resp = self.post_json(self.ai_url(), {"kind": "description", "notes": "Notas aqui"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertJSONEqual(resp.content, {"text": "TEXTO GERADO"})

        # Garante que chamou create() com o modelo esperado e estrutura de mensagens
        client_instance.responses.create.assert_called_once()
        called_kwargs = client_instance.responses.create.call_args.kwargs
        self.assertEqual(called_kwargs.get("model"), "gpt-5.2")
        self.assertIn("input", called_kwargs)
        self.assertEqual(called_kwargs["input"][0]["role"], "system")
        self.assertEqual(called_kwargs["input"][1]["role"], "user")

    @patch("report_maker.views.ai_textblock.OpenAI")
    def test_unknown_kind_falls_back_to_generic(self, OpenAIMock: Mock):
        self.login()

        fake_resp = Mock()
        fake_resp.output_text = "OK"

        client_instance = Mock()
        client_instance.responses.create.return_value = fake_resp
        OpenAIMock.return_value = client_instance

        resp = self.post_json(self.ai_url(), {"kind": "nao_existe", "notes": "Notas aqui"})
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {"text": "OK"})

    # ─────────────────────────────────────────────
    # Erros (patch de exceções para não depender da assinatura real do SDK)
    # ─────────────────────────────────────────────
    @patch("report_maker.views.ai_textblock.OpenAI")
    @patch("report_maker.views.ai_textblock.RateLimitError", new=type("DummyRateLimitError", (Exception,), {}))
    def test_rate_limit_error_returns_429(self, OpenAIMock: Mock):
        self.login()

        dummy_exc_cls = __import__("report_maker.views.ai_textblock", fromlist=["RateLimitError"]).RateLimitError
        client_instance = Mock()
        client_instance.responses.create.side_effect = dummy_exc_cls("rate limit")
        OpenAIMock.return_value = client_instance

        resp = self.post_json(self.ai_url(), {"kind": "generic", "notes": "abc"})
        self.assertEqual(resp.status_code, 429)
        body = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(body.get("error"), "insufficient_quota")

    @patch("report_maker.views.ai_textblock.OpenAI")
    @patch("report_maker.views.ai_textblock.AuthenticationError", new=type("DummyAuthError", (Exception,), {}))
    def test_auth_error_returns_401(self, OpenAIMock: Mock):
        self.login()

        dummy_exc_cls = __import__(
            "report_maker.views.ai_textblock", fromlist=["AuthenticationError"]
        ).AuthenticationError
        client_instance = Mock()
        client_instance.responses.create.side_effect = dummy_exc_cls("auth error")
        OpenAIMock.return_value = client_instance

        resp = self.post_json(self.ai_url(), {"kind": "generic", "notes": "abc"})
        self.assertEqual(resp.status_code, 401)
        body = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(body.get("error"), "auth_error")

    @patch("report_maker.views.ai_textblock.OpenAI")
    @patch("report_maker.views.ai_textblock.APIError", new=type("DummyAPIError", (Exception,), {}))
    def test_api_error_returns_503(self, OpenAIMock: Mock):
        self.login()

        dummy_exc_cls = __import__("report_maker.views.ai_textblock", fromlist=["APIError"]).APIError
        client_instance = Mock()
        client_instance.responses.create.side_effect = dummy_exc_cls("api error")
        OpenAIMock.return_value = client_instance

        resp = self.post_json(self.ai_url(), {"kind": "generic", "notes": "abc"})
        self.assertEqual(resp.status_code, 503)
        body = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(body.get("error"), "api_error")
