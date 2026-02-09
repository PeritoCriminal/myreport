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
    "Você redige textos técnicos periciais no contexto brasileiro. "
    "Adote um tom assertivo e impessoal (voz passiva com 'se'). "
    "Diferencie 'estado' (pretérito imperfeito: apresentava, estava) de 'ocorrência' (pretérito perfeito: verificou-se, constatou-se). "
    "Seja preciso, mas evite uma redação excessivamente truncada; o texto deve ter coesão e fluidez. "
    "Não utilize termos subjetivos nem invente dados."
)

# O que escrever (varia por campo)
KIND_PROMPTS = {
    "service_context": (
        "Redija o Contexto do Atendimento priorizando tópicos (Markdown lista não numerada). "
        "Estrutura: Inicie com frase curta sobre a preservação (ex.: 'Local preservado pela PM.'). "
        "Formatação Chave-Valor: Use '**Chave**: valor' (ex.: '**Encarregado**: Cabo PM Fulano'). "
        "Regras Verbais Rígidas: "
        "1. Pretérito Imperfeito para estados/ações contínuas durante o exame (ex.: 'A equipe PM isolava o local'); "
        "2. Pretérito Perfeito para fatos concluídos (ex.: 'O perito compareceu', 'A equipe foi recebida'). "
        "Agendamentos: Descreva quem recebeu a equipe, nome e função, mencionando a indicação do local e o acompanhamento dos trabalhos."
    ),
    "description": (
        "Descreva o objeto ou local em 1 ou 2 parágrafos técnicos. "
        "Utilize o Pretérito Imperfeito para características estruturais (ex.: 'O imóvel possuía', 'A via apresentava') "
        "e Pretérito Perfeito para alterações encontradas (ex.: 'O vidro foi quebrado'). "
        "Mantenha foco estritamente visual e material, sem juízo de valor."
    ),
    "observed_elements": (
        "Descreva os elementos observados de forma organizada, escolhendo o formato que melhor se adapte à complexidade das anotações: "
        "1. Para múltiplos itens isolados, utilize listas não numeradas (Markdown '- '); "
        "2. Para elementos que possuam relação entre si ou exijam detalhamento de posição/dinâmica, utilize parágrafos descritivos. "
        "Foque no substantivo e em sua condição técnica (ex.: 'Fragmentos de vidro incolor espalhados sobre o leito carroçável'). "
        "Mantenha a ordem lógica das anotações, preservando a conexão entre os vestígios encontrados."
    ),
    "weather_conditions": (
        "Descreva condições ambientais relevantes em parágrafo único. "
        "Use o Pretérito Imperfeito (ex.: 'O céu estava encoberto', 'A visibilidade era reduzida'). "
        "Se não houver dados nas anotações, responda 'Informação não constante nas anotações'."
    ),
    "road_conditions": (
        "Descreva o estado da via/pavimento em parágrafo curto. "
        "Diferencie estado (Imperfeito: 'O asfalto apresentava desgaste') de anomalias pontuais (Perfeito: 'Verificou-se mancha de óleo'). "
        "Foque em conservação, aderência e irregularidades."
    ),
    "traffic_signage": (
        "Descreva a sinalização viária conforme a estrutura: "
        "'A sinalização no trecho compreendia: – sinalização horizontal: [itens]; – sinalização vertical: [itens].' "
        "Utilize termos técnicos do [Código de Trânsito Brasileiro (CTB)](https://www.planalto.gov.br)."
    ),
    "generic": (
        "Redija texto técnico pericial curto. Use voz passiva, elimine pronomes desnecessários e mantenha o foco nos vestígios materiais."
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
