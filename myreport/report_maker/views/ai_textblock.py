# report_maker/views/ai_textblock.py
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from openai import OpenAI
from openai import RateLimitError, APIError, AuthenticationError


# Regras permanentes de estilo (vale para todos os tipos)
SYSTEM_STYLE = (
    "Você redige texto técnico pericial no contexto brasileiro. "
    "Utilize sempre o passado simples. "
    "Empregue linguagem objetiva, técnica e assertiva. "
    "Evite termos subjetivos como 'aparentemente', 'possivelmente' e 'provavelmente'. "
    "Não invente dados; utilize apenas o que estiver explicitamente nas anotações."
)

# O que escrever (varia por campo)
KIND_PROMPTS = {
    "service_context": (
        "Redija um único parágrafo curto (80 a 140 palavras) descrevendo o contexto do atendimento pericial, "
        "incluindo preservação e isolamento do local e o acompanhamento do exame, quando informado. "
        "Se houver, cite encarregado, equipe/órgão e viatura de forma objetiva. "
        "Não acrescente informações não contidas nas anotações."
    ),
    "description": (
        "Redija 1 a 2 parágrafos curtos descrevendo tecnicamente o objeto/local do exame, de forma objetiva, "
        "sem inferências e sem adjetivação desnecessária. "
        "Não acrescente informações não contidas nas anotações."
    ),
    "observed_elements": (
        "Converta as anotações em uma lista numerada (Markdown), com itens curtos e objetivos, "
        "mantendo apenas elementos efetivamente citados. "
        "Não acrescente informações não contidas nas anotações."
    ),
    "weather_conditions": (
        "Redija um parágrafo curto descrevendo as condições ambientais/climáticas relevantes ao exame "
        "(ex.: luminosidade, chuva, neblina, visibilidade), apenas se estiverem nas anotações. "
        "Não invente informações."
    ),
    "road_conditions": (
        "Redija um parágrafo curto descrevendo as condições de conservação da via/pavimento "
        "(ex.: estado geral, irregularidades, contaminantes), apenas com base nas anotações. "
        "Não invente informações."
    ),
    "traffic_signage": (
        "Redija um parágrafo curto descrevendo a sinalização viária, preferindo a estrutura 'incluindo: "
        "– sinalização horizontal: ...; – sinalização vertical: ...'. "
        "Use apenas o que constar nas anotações e não invente informações."
    ),
    "generic": (
        "Redija um texto técnico curto e objetivo com base nas anotações, sem inferências e sem inventar dados."
    ),
}


@login_required
@require_POST
def ai_textblock_generate(request):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    kind = (payload.get("kind") or "generic").strip()
    notes = (payload.get("notes") or "").strip()

    if not notes:
        return JsonResponse({"error": "notes_required"}, status=400)

    instruction = KIND_PROMPTS.get(kind, KIND_PROMPTS["generic"])

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        resp = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "user", "content": f"Instrução: {instruction}\n\nAnotações:\n{notes}"},
            ],
        )
        return JsonResponse({"text": resp.output_text})

    except RateLimitError:
        return JsonResponse(
            {"error": "insufficient_quota", "detail": "Sem cota/crédito na API. Verifique Billing/Plano."},
            status=429,
        )
    except AuthenticationError:
        return JsonResponse(
            {"error": "auth_error", "detail": "Chave inválida/ausente. Verifique OPENAI_API_KEY."},
            status=401,
        )
    except APIError:
        return JsonResponse(
            {"error": "api_error", "detail": "Erro temporário na API. Tente novamente."},
            status=503,
        )
