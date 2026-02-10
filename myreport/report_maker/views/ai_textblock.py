# report_maker/views/ai_textblock.py
import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from openai import OpenAI, RateLimitError, APIError, AuthenticationError


# Regras permanentes de estilo (vale para todos os tipos)
SYSTEM_STYLE = (
    "Você é um perito criminal redigindo laudos técnicos. "
    "Use tom assertivo, impessoal e linguagem culta brasileira. "
    "Diferencie 'estado' (imperfeito: estava) de 'ocorrência' (perfeito: verificou-se). "
    "Não invente dados."
)

# O que escrever (varia por campo)
KIND_PROMPTS = {
    "service_context": (
        "Redija o Contexto do Atendimento em tópicos (Markdown). "
        "Use '**Chave**: valor'. "
        "Finalize com a linha: *(Contexto de Serviço - Texto gerado com auxílio de IA)*"
    ),
    "description": (
        "Descreva o objeto/local tecnicamente em 1 ou 2 parágrafos. "
        "Finalize com a linha: *(Descrição - Texto gerado com auxílio de IA)*"
    ),
    "historic": (
        "Gere uma lista Markdown. Cada item: '- **DATA**: TEXTO'. "
        "Converta datas para 'dd de mmm de aaaa'. "
        "Importante: Após a lista, adicione uma linha em branco e obrigatoriamente o rodapé: "
        "*(Histórico - Texto gerado com auxilio de IA)*"
    ),
    "generic": (
        "Redija texto técnico pericial curto. "
        "Finalize com a linha: *(Texto gerado com auxílio de IA)*"
    ),
    # Adicione os demais conforme necessário, sempre repetindo a instrução do rodapé no final
}

@login_required
@require_POST
def ai_textblock_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    raw_kind = (payload.get("kind") or payload.get("placement") or "generic")
    
    # Mapeamento de normalização já existente
    KIND_ALIASES = {
        "HISTORIC": "historic",
        "SERVICE_CONTEXT": "service_context",
        "DESCRIPTION": "description",
        "GENERIC": "generic",
    }
    
    kind = KIND_ALIASES.get(str(raw_kind).upper(), str(raw_kind).lower())
    notes = (payload.get("notes") or "").strip()

    if not notes:
        return JsonResponse({"error": "notes_required"}, status=400)

    instruction = KIND_PROMPTS.get(kind, KIND_PROMPTS["generic"])

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        # CORREÇÃO: gpt-5.2 não existe. Usando gpt-4o para maior aderência a instruções.
        # CORREÇÃO: O método correto é chat.completions.create.
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "user", "content": f"Instrução: {instruction}\n\nAnotações:\n{notes}"},
            ],
            temperature=0.2, # Mantém a resposta técnica e menos criativa
        )
        
        generated_text = resp.choices[0].message.content.strip()
        return JsonResponse({"text": generated_text})

    except RateLimitError:
        return JsonResponse({"error": "insufficient_quota"}, status=429)
    except Exception as e:
        return JsonResponse({"error": "api_error", "detail": str(e)}, status=500)

