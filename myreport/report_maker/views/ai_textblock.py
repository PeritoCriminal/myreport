from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from openai import OpenAI

# Estes nomes PRECISAM existir no módulo porque os testes fazem patch neles.
# Não dependemos da assinatura real do SDK aqui; o teste injeta exceções "dummy".
try:  # pragma: no cover
    from openai import APIError, AuthenticationError, RateLimitError
except Exception:  # pragma: no cover
    class APIError(Exception):
        pass

    class AuthenticationError(Exception):
        pass

    class RateLimitError(Exception):
        pass


SYSTEM_STYLE = (
    #   Vamos deixar esse trecho comentado até resolvermos o problema, e depois que estiver
    #   rodando bem, aí instruimos a IA.
    #"Você é um perito criminal redigindo laudos técnicos. "
    #"Use tom assertivo, impessoal e linguagem culta brasileira. "
    #"Use preferencialmente passado simples. "
    #"NÃO acrescente informações que não estejam explicitamente contidas nas anotações. "
    #"Se faltar dado, omita — não presuma, não complete, não estime."
    #"Se o conteúdo for 'teste', retorne a string: conteúdo vazio."
)

KIND_PROMPTS: dict[str, str] = {
    "preamble": (
        "Se o conteúdo for 'teste', retorne a string: Prâmbulo."
        # Retorna Genérico
    ),
    "description": (
        "Se o conteúdo for 'teste', retorne a string: Descrição."
        # Retorna Descrição
    ),
    "methodology": (
        "Se o conteúdo for 'teste', retorne a string: Metodologia."
        # Retorna metodologia
    ),
    "examination": (
        "Se o conteúdo for 'teste', retorne a string: Exame."
        # Retorna Exame
    ),
    "results": (
        "Se o conteúdo for 'teste', retorne a string: Resultado."
        # Retorna Resultado
    ),
    "historic":(
        "Se o conteúdo for 'teste', retorne a string: Histórico."
        # Retorna Genérico
    ),
    "SUMMARY":(
        "Se o conteúdo for 'teste', retorne a string: Sumário."
        # Retorna Genérico?
    ),
    "observed_elements":(
        "Se o conteúdo for 'teste', retorne a string: Elementos_observados."
        # Retorna Elementos
    ),
    "operational_tests":(
         "Se o conteúdo for 'teste', retorne a string: Testes_operacionais."
         # Retorna Testes
    ),
    "tire_conditions":(
        "Se o conteúdo for 'teste', retorne a string: Peneus."
        # Retorna Penus
    ),
    "observation":(
        "Se o conteúdo for 'teste', retorne a string: Observações."
        # Retorna Observações
    ),
    "service_context":(
        "Se o conteúdo for 'teste', retorne a string: Contexto_de_atendimento."
        # Retorna Contexto
    ),
    "weather_conditions":(
        "Se o conteúdo for 'teste', retorne a string: Clima_condições."
        # Retorna Clima
    ),
    "road_conditions":(
        "Se o conteúdo for 'teste', retorne a string: Via_condições."
        # Retorna Via
    ),
    "traffic_signage":(
        "Se o conteúdo for 'teste', retorne a string: Sinalização."
        # Retorna Sinalização
    ),
    "generic": (
        "Se o conteúdo for 'teste', retorne a string: Genérico."
        # Retorna Genérico, e é aqui muitos caem por não estar mapeados, eu acho, e a IA não vai ficar boa se não tratarmos isso.
    ),
}


def _resolve_kind(raw_kind: str) -> str:
    k = (raw_kind or "").strip().lower()
    return k if k in KIND_PROMPTS else "generic"


@login_required
@require_POST
def ai_textblock_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    raw_kind = str(payload.get("kind") or payload.get("placement") or "generic")
    kind = _resolve_kind(raw_kind)

    notes = (payload.get("notes") or "").strip()
    if not notes:
        return JsonResponse({"error": "notes_required"}, status=400)

    instruction = KIND_PROMPTS.get(kind, KIND_PROMPTS["generic"])

    # ⚠️ Contrato dos testes:
    # - usar OpenAI().responses.create(...)
    # - passar model="gpt-5.2"
    # - passar input como lista de mensagens (system/user)
    # - retornar resp.output_text
    try:
        client = OpenAI()
        resp = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "user", "content": f"Instrução: {instruction}\n\nAnotações:\n{notes}"},
            ],
        )
        text = (getattr(resp, "output_text", "") or "").strip()
        return JsonResponse({"text": text}, status=200)

    except RateLimitError:
        # contrato do teste: 429 + error == "insufficient_quota"
        return JsonResponse({"error": "insufficient_quota"}, status=429)

    except AuthenticationError:
        return JsonResponse({"error": "auth_error"}, status=401)

    except APIError:
        return JsonResponse({"error": "api_error"}, status=503)

    except Exception as e:
        return JsonResponse({"error": "server_error", "detail": str(e)}, status=500)
