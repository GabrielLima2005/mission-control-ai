"""Thresholds e regras de decisao - Trilha EnviroSat.

Toda a logica de "e critico ou nao?" vive AQUI, em Python (nao no prompt da IA).
A IA serve para explicar e contextualizar o impacto terrestre; a decisao tecnica
e deterministica e auditavel neste modulo.

Camadas:
  1. avaliar(dados)          -> classifica cada parametro e gera alertas
  2. responder_automatico()  -> aciona respostas automatizadas para crises
"""
from __future__ import annotations

# Niveis de severidade (ordenados por gravidade crescente).
NORMAL = "NORMAL"
ATENCAO = "ATENCAO"
CRITICO = "CRITICO"

_ORDEM = {NORMAL: 0, ATENCAO: 1, CRITICO: 2}

# Limiares (thresholds) de decisao por parametro.
LIMIARES = {
    "temp_payload_c": {"atencao": 40.0, "critico": 60.0},
    "energia_bateria_pct": {"atencao": 35.0, "critico": 20.0},  # quanto MENOR, pior
    "buffer_imagens_pct": {"atencao": 80.0, "critico": 90.0},
    "precisao_geo_m": {"atencao": 30.0, "critico": 50.0},
}

# A partir de quantos focos termicos tratamos como EVENTO de incendio relevante.
LIMIAR_FOCOS_EVENTO = 30


def _novo_alerta(parametro: str, severidade: str, valor, mensagem: str) -> dict:
    return {
        "parametro": parametro,
        "severidade": severidade,
        "valor": valor,
        "mensagem": mensagem,
    }


def avaliar(dados: dict) -> dict:
    """Avalia o snapshot de telemetria e retorna alertas + severidade geral.

    Returns:
        dict com chaves: alertas (list), severidade_geral (str),
        evento_incendio (bool).
    """
    alertas: list[dict] = []

    # --- Temperatura do payload (quanto MAIOR, pior) ---
    temp = dados["temp_payload_c"]
    lim = LIMIARES["temp_payload_c"]
    if temp >= lim["critico"]:
        alertas.append(_novo_alerta(
            "temp_payload_c", CRITICO, temp,
            f"Temperatura do payload em {temp:.1f}C - risco de dano permanente ao sensor optico/termico.",
        ))
    elif temp >= lim["atencao"]:
        alertas.append(_novo_alerta(
            "temp_payload_c", ATENCAO, temp,
            f"Temperatura do payload elevada ({temp:.1f}C) - acima da faixa nominal.",
        ))

    # --- Energia da bateria (quanto MENOR, pior) ---
    energia = dados["energia_bateria_pct"]
    lim = LIMIARES["energia_bateria_pct"]
    if energia <= lim["critico"]:
        alertas.append(_novo_alerta(
            "energia_bateria_pct", CRITICO, energia,
            f"Carga da bateria em {energia:.1f}% - risco de desligamento de subsistemas.",
        ))
    elif energia <= lim["atencao"]:
        alertas.append(_novo_alerta(
            "energia_bateria_pct", ATENCAO, energia,
            f"Carga da bateria baixa ({energia:.1f}%) - margem reduzida para a proxima orbita.",
        ))

    # --- Sensor termico (estado discreto) ---
    sensor = dados["sensor_termico"]
    if sensor == "offline":
        alertas.append(_novo_alerta(
            "sensor_termico", CRITICO, sensor,
            "Sensor termico OFFLINE - missao cega para deteccao de focos de incendio.",
        ))
    elif sensor == "degradado":
        alertas.append(_novo_alerta(
            "sensor_termico", ATENCAO, sensor,
            "Sensor termico DEGRADADO - sensibilidade reduzida, risco de falso negativo.",
        ))

    # --- Buffer de imagens (quanto MAIOR, pior) ---
    buffer = dados["buffer_imagens_pct"]
    lim = LIMIARES["buffer_imagens_pct"]
    if buffer >= lim["critico"]:
        alertas.append(_novo_alerta(
            "buffer_imagens_pct", CRITICO, buffer,
            f"Buffer de imagens em {buffer:.1f}% - iminente perda de dados por sobrescrita.",
        ))
    elif buffer >= lim["atencao"]:
        alertas.append(_novo_alerta(
            "buffer_imagens_pct", ATENCAO, buffer,
            f"Buffer de imagens alto ({buffer:.1f}%) - priorizar proximo downlink.",
        ))

    # --- Precisao de geolocalizacao (quanto MAIOR o erro, pior) ---
    geo = dados["precisao_geo_m"]
    lim = LIMIARES["precisao_geo_m"]
    if geo >= lim["critico"]:
        alertas.append(_novo_alerta(
            "precisao_geo_m", CRITICO, geo,
            f"Erro de geolocalizacao em {geo:.1f}m - coordenadas de focos nao confiaveis.",
        ))
    elif geo >= lim["atencao"]:
        alertas.append(_novo_alerta(
            "precisao_geo_m", ATENCAO, geo,
            f"Erro de geolocalizacao elevado ({geo:.1f}m) - recomenda recalibrar atitude.",
        ))

    # --- Evento de incendio (nao e falha do satelite, e dado operacional) ---
    focos = dados.get("focos_detectados", 0)
    evento_incendio = focos >= LIMIAR_FOCOS_EVENTO
    if evento_incendio:
        alertas.append(_novo_alerta(
            "focos_detectados", ATENCAO, focos,
            f"{focos} focos termicos detectados na ultima passagem - acionar protocolo de incendio.",
        ))

    severidade_geral = NORMAL
    for a in alertas:
        if _ORDEM[a["severidade"]] > _ORDEM[severidade_geral]:
            severidade_geral = a["severidade"]

    return {
        "alertas": alertas,
        "severidade_geral": severidade_geral,
        "evento_incendio": evento_incendio,
    }


def responder_automatico(dados: dict, avaliacao: dict) -> list[str]:
    """Aciona respostas automatizadas (em codigo) diante de situacoes criticas.

    Estas acoes simulam comandos enviados pelo computador de bordo SEM esperar
    a IA - a IA apenas explica depois o que aconteceu e por que.
    """
    acoes: list[str] = []

    temp = dados["temp_payload_c"]
    energia = dados["energia_bateria_pct"]
    buffer = dados["buffer_imagens_pct"]
    sensor = dados["sensor_termico"]
    geo = dados["precisao_geo_m"]

    if temp >= LIMIARES["temp_payload_c"]["critico"]:
        acoes.append(
            "MODO PROTECAO TERMICA: duty cycle do payload reduzido e radiador "
            "reorientado para dissipar calor."
        )
    if energia <= LIMIARES["energia_bateria_pct"]["critico"]:
        acoes.append(
            "MODO ECONOMIA DE ENERGIA: sensor optico RGB desligado, prioridade "
            "para o sensor termico (deteccao de focos) ate recarga solar."
        )
    if buffer >= LIMIARES["buffer_imagens_pct"]["critico"]:
        acoes.append(
            "DOWNLINK PRIORITARIO: imagens redundantes descartadas e fila "
            "reordenada para transmitir tiles com focos primeiro."
        )
    if sensor == "offline":
        acoes.append(
            "FAILOVER DE SENSOR: reset agendado do sensor termico e notificacao "
            "ao centro de controle (INPE) sobre janela cega."
        )
    if geo >= LIMIARES["precisao_geo_m"]["critico"]:
        acoes.append(
            "RECALIBRACAO DE ATITUDE: star tracker secundario acionado para "
            "restaurar a precisao de geolocalizacao."
        )
    if avaliacao.get("evento_incendio"):
        acoes.append(
            "PROTOCOLO DE INCENDIO: alerta georreferenciado encaminhado as "
            "brigadas estaduais e ao painel do IBAMA."
        )

    if not acoes:
        acoes.append("Nenhuma acao automatica necessaria - missao em operacao nominal.")
    return acoes


def formatar_alertas(avaliacao: dict) -> str:
    """Formata os alertas em texto legivel para o terminal."""
    if not avaliacao["alertas"]:
        return "  Nenhum alerta - todos os parametros dentro da faixa nominal."
    linhas = []
    icones = {NORMAL: "[ok]", ATENCAO: "[!]", CRITICO: "[X]"}
    for a in avaliacao["alertas"]:
        linhas.append(f"  {icones.get(a['severidade'], '[?]')} {a['severidade']:<8} {a['mensagem']}")
    return "\n".join(linhas)
