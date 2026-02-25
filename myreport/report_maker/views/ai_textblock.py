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

# ============================================================
# TODO – Implementar análise automatizada de imagens por IA
# ============================================================
#
# Implementar, oportunamente, módulo de leitura e interpretação
# automatizada de imagens pela IA, integrado ao fluxo do
# ai_textblock, permitindo:
#
# - Extração de elementos visuais relevantes (vestígios, danos,
#   manchas, disposições espaciais, objetos e estruturas).
# - Geração de descrição técnica baseada exclusivamente no
#   conteúdo visual objetivamente identificado.
# - Aplicação automática das diretrizes verbais padronizadas
#   do projeto (pretérito imperfeito para estados contínuos,
#   pretérito perfeito para atos pontuais e presente impessoal
#   na conclusão).
# - Integração com o ImageReportModel para análise individual
#   ou em lote.
# - Possibilidade de validação humana antes da incorporação
#   definitiva ao laudo.
# - Registro de rastreabilidade (imagem analisada, data,
#   versão do modelo utilizado).
#
# Observação:
# A funcionalidade deverá respeitar o princípio da não inferência,
# limitando-se à descrição de elementos objetivamente identificáveis,
# vedada qualquer suposição não suportada pela imagem.
#
# Status: Planejado para implementação futura.
# ============================================================

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
    "Se faltar dado, omita — não presuma, não complete, não estime. "
    "Não utilize termos como 'aparentemente', 'possivelmente', 'provavelmente'."
)

TENSE_STYLE = (
    "DIRETRIZES VERBAIS (OBRIGATÓRIAS): "
    "1) Use pretérito imperfeito para estados e condições contínuas ou características observadas "
    "(ex.: 'o local encontrava-se...', 'a via apresentava...', 'a ponte exibia...'). "
    "2) Use pretérito perfeito para atos pontuais praticados "
    "(ex.: 'foram coletadas...', 'realizou-se...', 'registrou-se...'). "
    "3) Na conclusão, utilize presente impessoal "
    "(ex.: 'conclui-se que', 'evidencia-se que', 'verifica-se que'). "
    "4) Sempre que possível, descreva o estado do local em vez da ação do agente "
    "(prefira 'o local encontrava-se preservado' a 'a equipe preservou/preservava')."
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
    Gera texto pericial com filtragem seletiva de contexto.
    Para conclusões, utiliza apenas dados de materialidade para evitar 
    repetição de estruturas de tópicos e focar na síntese discursiva.
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    raw_kind = payload.get("kind") or payload.get("placement") or "generic"
    kind = _resolve_kind(str(raw_kind))
    notes = (payload.get("notes") or "").strip()
    report_id = (payload.get("report_id") or "").strip()

    # --- 1. COLETA ESTRUTURADA (Dicionário de Contexto) ---
    report_data = {"general": {}, "objects": []}
    
    if report_id:
        this_report = get_object_or_404(ReportCase, pk=report_id, author=request.user)
        report_data["general"] = {
            "descricao": getattr(this_report, 'description', ''),
            "exames": getattr(this_report, 'examination', '')
        }

        for obj in this_report.exam_objects.all():
            actual_obj = obj.concrete
            report_data["objects"].append({
                "tipo": actual_obj._meta.verbose_name,
                "description": getattr(actual_obj, 'description', '').strip(),
                "observed_elements": getattr(actual_obj, 'observed_elements', '').strip(),
                "service_context": getattr(actual_obj, 'service_context', '').strip(),
            })

    # --- 2. FILTRAGEM SELETIVA PARA O PROMPT ---
    # Se for conclusão, ignorar 'service_context' e 'tipo' para não viciar o texto
    # --- 2. FILTRAGEM SELETIVA PARA O PROMPT ---
    if kind == "conclusion":
        # Extraímos apenas o essencial da materialidade para o contexto
        raw_materiality = [f"{o['tipo']}: {o['description']} | Vestígios: {o['observed_elements']}" for o in report_data["objects"]]
        context_for_ai = "\n".join(raw_materiality)
        
        role_behavior = "AJA COMO PERITO CRIMINAL SÉNIOR EMITINDO PARECER FINAL INTERPRETATIVO."
        
        # Construção de um prompt focado em síntese e não em repetição
        user_message = (
            f"DADOS DE APOIO (Contexto dos Vestígios):\n{context_for_ai}\n\n"
            f"NOTAS ADICIONAIS DO PERITO: {notes if notes else 'Nenhuma.'}\n\n"
            "TAREFA: Redija a CONCLUSÃO do laudo pericial seguindo estas diretrizes rigorosas:\n"
            "1. NÃO REPITA descrições detalhadas, placas, modelos ou cores que já constam no corpo do laudo.\n"
            "2. SÍNTESE INTERPRETATIVA: Em vez de listar 'o que havia', explique 'o que isso significa' tecnicamente.\n"
            "3. EVITE REDUNDÂNCIA: Se o dado já está nos 'Dados de Apoio', use-o apenas para fundamentar a lógica, não para transcrevê-lo novamente.\n"
            "4. ESTILO: Texto discursivo, fluido, sem tópicos, focando na dinâmica ou na constatação final (ex: 'os danos são congruentes com...', 'evidencia-se a materialidade de...').\n"
            "5. OBRIGATÓRIO: Inicie com 'Conforme se extrai do exame do local e dos vestígios observados, conclui-se que...'\n"
            "6. OBRIGATÓRIO: Encerre com '*Nada mais havendo a consignar, encerra-se o presente laudo.*'"
        )
    else:
        # Para outras seções, mantemos o contexto completo para auxílio
        full_context = f"{report_data['general'].get('descricao')}\n"
        for o in report_data["objects"]:
            full_context += f"- {o['tipo']}: {o['description']} {o['observed_elements']}\n"
        
        context_for_ai = full_context
        role_behavior = "AJA COMO ASSISTENTE TÉCNICO PERICIAL."
        user_message = f"CONTEXTO: {context_for_ai}\n\nSEÇÃO: {kind}\nTEXTO ATUAL: {notes}\nTAREFA: Refine ou sugira o texto para esta seção."

    # --- 3. CHAMADA À API ---
    try:
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "system", "content": TENSE_STYLE},
                {"role": "system", "content": role_behavior},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1
        )
        return JsonResponse({"text": resp.choices[0].message.content.strip()}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)