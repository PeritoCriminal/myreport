# path: myreport/report_maker/views/ai_textblock.py

from __future__ import annotations

from report_maker.models import ReportCase
from django.shortcuts import get_object_or_404

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
    "Você é um perito criminal redigindo laudos técnicos. "
    "Use tom assertivo, impessoal e linguagem culta brasileira. "
    "NÃO acrescente informações que não estejam explicitamente contidas nas anotações. "
    "Se faltar dado, omita — não presuma, não complete, não estime."
)

KIND_PROMPTS: dict[str, str] = {
    "preamble": (
        "Sua tarefa é redigir ou corrigir o preâmbulo oficial do laudo pericial. "
        "Mantenha rigorosamente o padrão institucional: 'Aos [data], na cidade de [cidade] e na Superintendência da "
        "Polícia Técnico Científica, no Núcleo de Perícias Criminalísticas de Americana, em conformidade com o disposto "
        "no artigo 178 do Decreto-Lei nº 3.689, de 3 de outubro de 1941, foi designado o Perito Criminal [Nome do Perito] "
        "para proceder ao exame pericial, em atendimento à requisição expedida pelo Exmo. Sr. Delegado de Polícia [Nome do Delegado].' "
        "INSTRUÇÕES: 1. Se o texto fornecido já estiver nesse padrão, corrija apenas erros de concordância, regência e pontuação. "
        "2. Certifique-se de que os nomes próprios e datas estejam com iniciais maiúsculas. "
        "3. Mantenha a citação legal do Art. 178 do CPP intacta. "
        "4. Se as notas forem fragmentadas, organize-as dentro desta estrutura formal."
    ),
    "description": (
        # Aqui pode começar com uma frase como 'O local do exame compreendia um imóvel, 
        # ou um trecho de rodovia, ou uma área aberta situada em bla bla bla', 
        # Ou o 'objeto do exame consistia em bla bla bla'
        # seria interessante o sistema fazer uma busca nas últimas 10 descrições e ver como
        # é o estilo do usuário. 
    ),
    "methodology": (
        # preferencialemnte um texto atemporal como:
        # Detecção de sangue latente,
        # Ou levantamento de local com auxilio de drone
        # quimioluminescência
    ),
    "examination": (
        # Descrever como é realizado o exame
    ),
    "results": (
        # positivo / negativo / inconclusivo para tal situação, em geral
        # o que foi quesitado na requisição de exame.
    ),
    "historic":(
        # preferencialmente uma lista não numerada, contendo data e descrição do que foi realizado
        # pode ser em tempo neutro, por exemlo:
        # 10 de janeiro de 2026 - Recebimento da requisição
        # 11 de janeiro de 2026 - Designação do perito responsavel
        # 13 de janeiro de 2026 - Visita técnica ao local dos fatos
        # 25 de janeiro de 2026 - Emissão do laudo pericial
    ),
    "summary":(
        # Aqui é interessante já ter o laudo praticamente pronto,
        # rodar o arquivo que gera o pdf apenas para determinar a numeração dos
        # títulos e subtítulos e suas respectivas páginas no pdf. 
    ),
    "observed_elements":(
        # De preferênica uma lista não numerada como abaixo:
        # - Portão danificado: o portão de acesso para veículos apresentava uma fratura bla bla bla
        # - Manchas hemáticas: sobre o piso da cozinha encontravam-se manhcas de aspecto hemático bla bla bla
        # - Subtração da televisão: sobre a supefície empoeirada da estante, havia uma área sem sujidade que 
        # formava uma silhueta com fomrato consistente com a base do pedestal de uma aparelho de televisão, indcando 
        # sua remoção recente bla bla bla 
    ),
    "operational_tests":(
         # algo do tipo, foram realizados testes operacionais e todos os sistemas funcionarm a contento
         # ou não foram realizados testes operacionais,
         # ou, com excessão do sistema de freios, todos os sistemas estavam operantes e funcionaram conforme esperado
    ),
    "tire_conditions":(
        # Os pneus não paresentavam desgate signiticativo de suas bandas de rodagem ou
        # os pneus apresentavam desgate severo de suas bandas de rodagem, além limite do indicador TWI
    ),
    "observation":(
        # Corrija erros gramaticais, incluindo erros de concordância e regência
    ),
    "service_context":(
        # Algo do tipo: Quando da realização do exame, a equipe pericial foi recebida pelo Sr. ou pela Sra.
        # Pessoa tal, que se apresentou como funcionário do estabelecimento, morador do imóvel, inquilino, chefe.
        # Essa pessoa franqueou a entrada da equipe, ou recebeu a equipe, deu informes ou prestou declarações, indicou o local
        # eacompanhou o exame pericial, ou o trabalho da equipe.
    ),
    "weather_conditions":(
        # condições climáticas, fatores que poderiam atrapalhar ou não a visibilidade no momento do evento examinado.
    ),
    "road_conditions":(
        # condições de manutenção e conservação da via.
    ),
    "traffic_signage":(
        # Apresentava sinalização viária adequada / inconsistente em relação à via, 
        # nítida / esmaecida / apagada, de forma que era possivel ver, ou não era possivel, incluindo:
        # - Sinalização horizontal: bla bla bla
        # - Sinalização vertical: bla bla bla
        # outras formas de sinaliação viária, se houver
    ),
    "generic": (
        # Retorna Genérico,
    ),
    "conclusion":(
        # aqui seria interessante ter o arquivo finalizado e, com base no arquivo e nos elementos observados,
    )
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

    # report_id passa a ser opcional (frontend manda; testes antigos não)
    report_id = (payload.get("report_id") or "").strip()
    this_report = None
    past_reports = ReportCase.objects.none()

    if report_id:
        this_report = get_object_or_404(ReportCase, pk=report_id, author=request.user)
        past_reports = (
            ReportCase.objects.filter(author=request.user)
            .exclude(pk=this_report.pk)
            .order_by("-created_at")[:10]
        )

    instruction = KIND_PROMPTS.get(kind, KIND_PROMPTS["generic"])

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
        return JsonResponse({"error": "insufficient_quota"}, status=429)
    except AuthenticationError:
        return JsonResponse({"error": "auth_error"}, status=401)
    except APIError:
        return JsonResponse({"error": "api_error"}, status=503)
    except Exception as e:
        return JsonResponse({"error": "server_error", "detail": str(e)}, status=500)
