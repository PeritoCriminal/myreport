# path: myreport/report_maker/views/ai_textblock.py

from __future__ import annotations
import json
import os
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from report_maker.models import ReportCase
from openai import OpenAI

# Configuração de exceções para garantir compatibilidade com os testes unitários
try:
    from openai import APIError, AuthenticationError, RateLimitError
except ImportError:
    class APIError(Exception): pass
    class AuthenticationError(Exception): pass
    class RateLimitError(Exception): pass

# --- CONFIGURAÇÕES DE ESTILO E PROMPTS ---

SYSTEM_STYLE = (
    "Você é um perito criminal redigindo laudos técnicos. "
    "Use tom assertivo, impessoal e linguagem culta brasileira. "
    "NÃO acrescente informações que não estejam explicitamente contidas nas anotações. "
    "Se faltar dado, omita — não presuma, não complete, não estime."
)

KIND_PROMPTS: dict[str, str] = {
    "preamble": (
        "Redija ou corrija o preâmbulo oficial do laudo. "
        "Padrão: 'Aos [data], na cidade de [cidade]... foi designado o Perito Criminal [Nome]...' "
        "Mantenha a citação do Art. 178 do CPP intacta."
    ),
    "description": (
        "Descreva o local ou objeto do exame. "
        "CASO VAZIO: Pergunte se é via pública, imóvel, objeto, arma ou cadáver. "
        "Sugira inícios como: 'O local do exame compreendia um imóvel...' ou 'O objeto consistia em...'"
    ),
    "methodology": (
        "Descreva os métodos científicos aplicados (ex: Drone, Reagentes, Fotogrametria). "
        "CASO VAZIO: Pergunte quais equipamentos ou técnicas foram utilizados e ofereça modelos para levantamento de local."
    ),
    "examination": (
        "Descreva minuciosamente como o exame foi realizado. "
        "CASO VAZIO: Explique que aqui deve constar a cronologia dos exames e as técnicas de busca de vestígios."
    ),
    "results": (
        "Apresente os resultados (positivo/negativo/inconclusivo). "
        "CASO VAZIO: Pergunte qual foi a constatação principal em relação ao que foi quesitado."
    ),
    "historic": (
        "Relate o histórico dos fatos em lista não numerada (Data - Evento). "
        "CASO VAZIO: Sugira o formato: '10/01/2026 - Recebimento da requisição'."
    ),
    "observed_elements": (
        "Liste os elementos observados (vestígios). Use Markdown (negrito nos títulos). "
        "EXEMPLO: '- **Portão danificado**: o acesso apresentava...' "
        "CASO VAZIO: Pergunte se houve arrombamento, manchas ou objetos desalojados."
    ),
    "operational_tests": (
        "Relate testes de funcionamento. "
        "EXEMPLOS: 'Sistemas funcionaram a contento', 'Não realizados por [motivo]', 'Exceção ao sistema de freios...'. "
        "CASO VAZIO: Ofereça estas três opções como guia."
    ),
    "tire_conditions": (
        "Descreva o estado dos pneus e indicador TWI. "
        "CASO VAZIO: Pergunte se os pneus estavam conservados ou com desgaste severo."
    ),
    "service_context": (
        "Relate quem recebeu a equipe no local. "
        "PADRÃO: 'A equipe foi recebida pelo Sr(a). [Nome], que se apresentou como [Função].' "
        "CASO VAZIO: Solicite o nome da pessoa e o que ela informou à equipe."
    ),
    "weather_conditions": (
        "Descreva o clima e visibilidade. "
        "CASO VAZIO: Pergunte se estava sol/chuva e se era dia/noite."
    ),
    "road_conditions": (
        "Descreva a conservação da pista (buracos, sulcos, ondulações). "
        "CASO VAZIO: Pergunte se a via estava íntegra ou se havia defeitos no pavimento."
    ),
    "traffic_signage": (
        "Descreva sinalização Vertical (placas) e Horizontal (solo). "
        "CASO VAZIO: Pergunte se as faixas e placas eram nítidas ou estavam apagadas."
    ),
    "observation": (
        "Revisão gramatical e anotações extras. "
        "CASO VAZIO: Explique que este campo serve para informações que não se encaixam nos outros."
    ),
    "conclusion": (
        "Sua tarefa é sintetizar os achados do laudo em uma conclusão pericial técnica. "
        "DIRETRIZES: \n"
        "1. Utilize os dados dos objetos e locais descritos (ex: rodovias, km, danos). \n"
        "2. Inicie OBRIGATORIAMENTE com: 'Conforme se extrai do exame do local e dos vestígios observados, conclui-se que...' \n"
        "3. Não apenas descreva o local, mas aponte a dinâmica ou a constatação final do exame. \n"
        "4. Encerre OBRIGATORIAMENTE com a frase exata: '*Nada mais havendo a consignar, encerra-se o presente laudo*.' (em itálico)."
    ),
    "generic": (
        "Você é um assistente técnico pericial. Se o campo estiver vazio, "
        "seja amigável e pergunte sobre o que se trata o exame para sugerir um modelo técnico."
    )
}

# --- FUNÇÕES AUXILIARES ---

def _resolve_kind(raw_kind: str) -> str:
    """Garante que o 'kind' recebido exista no dicionário, senão usa 'generic'."""
    k = (raw_kind or "").strip().lower()
    return k if k in KIND_PROMPTS else "generic"

# --- VIEW PRINCIPAL ---
@login_required
@require_POST
def ai_textblock_generate(request):
    """
    View principal para geração de texto pericial.
    Lógica: 
    1. Se houver 'notes', a IA atua como redatora técnica.
    2. Se 'notes' estiver vazio, a IA atua como tutora/assistente.
    3. Para a 'conclusion', a IA lê o conteúdo do laudo e de seus objetos (ExamObjects).
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    raw_kind = str(payload.get("kind") or payload.get("placement") or "generic")
    kind = _resolve_kind(raw_kind)
    notes = (payload.get("notes") or "").strip()
    report_id = (payload.get("report_id") or "").strip()

    # --- INJEÇÃO DE CONTEXTO DO LAUDO E OBJETOS CONCRETOS ---
    report_context_str = ""
    if report_id:
        this_report = get_object_or_404(ReportCase, pk=report_id, author=request.user)
        
        # Coletamos dados do laudo em si
        report_context_str = (
            f"\n--- CONTEXTO DO LAUDO ---\n"
            f"Descrição Geral: {getattr(this_report, 'description', 'Não preenchido')}\n"
            f"Exames Realizados: {getattr(this_report, 'examination', 'Não preenchido')}\n"
        )

        # AGORA: Buscamos os objetos concretos (ExamObject) via related_name
        # Usamos uma lista para construir o texto de cada objeto encontrado
        this_report_objects = this_report.exam_objects.all()
        
        if this_report_objects.exists():
            report_context_str += "\n--- OBJETOS EXAMINADOS NO LAUDO ---\n"
            for i, obj in enumerate(this_report_objects, 1):
                # Pegamos os campos description e observed_elements (do Mixin)
                # O getattr é essencial aqui porque nem todo objeto terá o Mixin aplicado
                d = getattr(obj, 'description', '').strip()
                o = getattr(obj, 'observed_elements', '').strip()
                
                if d or o:
                    report_context_str += f"Objeto {i}:\n"
                    if d: report_context_str += f"  - Descrição: {d}\n"
                    if o: report_context_str += f"  - Elementos Observados: {o}\n"

    # Busca a instrução específica no dicionário
    instruction = KIND_PROMPTS.get(kind, KIND_PROMPTS["generic"])

    # --- CONSTRUÇÃO DINÂMICA DO PROMPT ---
    if not notes:
        # MODO TUTOR: Campo vazio
        if kind == "conclusion":
            role_behavior = "AJA COMO UM PERITO SÉNIOR PROPONDO UMA CONCLUSÃO FINAL."
            user_message = (
                f"O perito solicitou uma proposta de conclusão baseada nos dados do laudo e dos objetos examinados:\n"
                f"{report_context_str}\n"
                "Instrução: Formule uma conclusão técnica, lógica e elegante. "
                "Siga as regras de início e fim (itálico) definidas na sua instrução específica."
            )
        else:
            role_behavior = "AJA COMO UM ASSISTENTE/TUTOR TÉCNICO."
            user_message = (
                f"O perito está na seção '{kind}' e o campo está vazio. "
                f"Considere o contexto atual do laudo: {report_context_str}\n"
                "Explique o que deve constar nesta seção e ofereça exemplos para ajudá-lo a começar."
            )
    else:
        # MODO REDATOR: O perito forneceu anotações
        role_behavior = "AJA COMO UM REDATOR TÉCNICO PERICIAL."
        user_message = (
            f"CONTEXTO DO LAUDO E OBJETOS:{report_context_str}\n"
            f"INSTRUÇÃO DA SEÇÃO: {instruction}\n"
            f"ANOTAÇÕES DO PERITO PARA FORMATAR:\n{notes}"
        )

    try:
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "system", "content": role_behavior},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6
        )
        
        generated_text = resp.choices[0].message.content.strip()
        return JsonResponse({"text": generated_text}, status=200)

    except RateLimitError:
        return JsonResponse({"error": "insufficient_quota"}, status=429)
    except AuthenticationError:
        return JsonResponse({"error": "auth_error"}, status=401)
    except Exception as e:
        # Retorna o erro detalhado para debug
        return JsonResponse({
            "error": "server_error", 
            "detail": str(e)
        }, status=500)