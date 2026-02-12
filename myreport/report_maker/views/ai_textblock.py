# report_maker/views/ai_textblock.py
import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from openai import OpenAI

SYSTEM_STYLE = (
    "Você é um perito criminal redigindo laudos técnicos. "
    "Use tom assertivo, impessoal e linguagem culta brasileira. "
    "Use preferencialmente passado simples. "
    "Diferencie 'estado' (imperfeito: estava) de 'ocorrência' (perfeito: verificou-se). "
    "NÃO acrescente informações que não estejam explicitamente contidas nas anotações. "
    "Se faltar dado, omita — não presuma, não complete, não estime. "
)

KIND_PROMPTS = {
    "historic": (
        "Gere uma lista Markdown. Cada item: '- **DATA**: TEXTO'. "
        "As datas são chaves; o histórico é o valor. "
        "Converta datas para 'dd de mmm de aaaa'. "
        "Se a data resultante ficar posterior à data atual, use o ano anterior. "
        "Se a data não trouxer ano, considere o ano atual. "
        "Não inclua fatos que não estejam explicitamente nas anotações. "
        "Finalize com: *(Histórico - Texto gerado com auxílio de IA)*"
    ),
    "summary": (
        "Redija um resumo executivo dos fatos. "
        "Finalize com: *(Resumo - Texto gerado com auxílio de IA)*"
    ),
    "observations": (
        "Redija observações técnicas colhidas na diligência. "
        "Finalize com: *(Observações - Texto gerado com auxílio de IA)*"
    ),
    "conclusion": (
        "Redija a conclusão pericial objetiva. "
        "Finalize com: *(Conclusão - Texto gerado com auxílio de IA)*"
    ),
    "description": (
        "Descreva o objeto/local tecnicamente em 1 ou 2 parágrafos. "
        "Finalize com: *(Descrição - Texto gerado com auxílio de IA)*"
    ),
    "service_context": (
        "Redija o Contexto do Atendimento em tópicos (Markdown). Use '**Chave**: valor'. "
        "Finalize com: *(Contexto de Serviço - Texto gerado com auxílio de IA)*"
    ),
    "generic": (
        "Redija um texto técnico pericial curto. "
        "Finalize com: *(Texto gerado com auxílio de IA)*"
    ),
}

@login_required
@require_POST
def ai_textblock_generate(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    # 1. Captura o que vem do frontend (pode ser HISTORIC, Histórico, historic, etc)
    raw_kind = str(payload.get("kind") or payload.get("placement") or "generic").strip()
    
    # 2. Mapeamento de sinônimos para garantir que tudo aponte para as chaves do KIND_PROMPTS
    # Transformamos a busca em algo insensível a maiúsculas/minúsculas e acentos comuns
    lookup = raw_kind.upper()
    
    MAP = {
        "HISTORIC": "historic",
        "HISTÓRICO": "historic",
        "SUMMARY": "summary",
        "RESUMO": "summary",
        "OBSERVATIONS": "observations",
        "OBSERVAÇÕES": "observations",
        "CONCLUSION": "conclusion",
        "CONCLUSÃO": "conclusion",
        "DESCRIPTION": "description",
        "DESCRIÇÃO": "description",
        "SERVICE_CONTEXT": "service_context",
        "CONTEXTO DO ATENDIMENTO": "service_context",
        "RESULTS": "conclusion",
    }

    # Tenta achar no mapa, se não achar, usa o lower do que veio, se não, generic
    target_key = MAP.get(lookup, raw_kind.lower())
    instruction = KIND_PROMPTS.get(target_key, KIND_PROMPTS["generic"])

    notes = (payload.get("notes") or "").strip()
    if not notes:
        return JsonResponse({"error": "notes_required"}, status=400)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "user", "content": f"Instrução: {instruction}\n\nAnotações:\n{notes}"},
            ],
            temperature=0.2,
        )
        return JsonResponse({"text": resp.choices[0].message.content.strip()})
    except Exception as e:
        return JsonResponse({"error": "api_error", "detail": str(e)}, status=500)