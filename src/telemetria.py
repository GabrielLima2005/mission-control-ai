"""Geracao de dados simulados de telemetria - Trilha EnviroSat.

Satelite simulado: observacao ambiental com sensor termico + optico
(similar a Amazonia-1 / Landsat), em orbita baixa heliossincrona.

Parametros monitorados (5):
  - temp_payload_c       : temperatura do payload optico/termico (C)
  - energia_bateria_pct  : carga disponivel da bateria (%)
  - sensor_termico       : saude do sensor termico de deteccao de focos
  - buffer_imagens_pct   : ocupacao do buffer de imagens nao transmitidas (%)
  - precisao_geo_m       : erro de geolocalizacao das imagens (metros)

A telemetria pode ser gerada aleatoriamente (coerente com o cenario) ou lida
de cenarios pre-definidos em data/cenarios.json. Nao e cientificamente exata,
apenas plausivel e coerente com o contexto da missao.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

# Faixas nominais de operacao (usadas pela camada de alertas tambem).
FAIXAS_NOMINAIS = {
    "temp_payload_c": (-10.0, 35.0),
    "energia_bateria_pct": (40.0, 100.0),
    "buffer_imagens_pct": (0.0, 80.0),
    "precisao_geo_m": (0.0, 30.0),
}

# Estados possiveis do sensor termico (ordenados do melhor para o pior).
ESTADOS_SENSOR = ("operacional", "degradado", "offline")

# Cenarios sinteticos para testes determinsticos (forcam situacoes extremas).
CENARIOS = {
    "normal": {
        "temp_payload_c": (5.0, 25.0),
        "energia_bateria_pct": (70.0, 98.0),
        "sensor_termico": "operacional",
        "buffer_imagens_pct": (10.0, 55.0),
        "precisao_geo_m": (5.0, 18.0),
        "focos_detectados": (0, 3),
        "janela_downlink_min": (8, 45),
    },
    "incendio_detectado": {
        "temp_payload_c": (15.0, 30.0),
        "energia_bateria_pct": (60.0, 90.0),
        "sensor_termico": "operacional",
        "buffer_imagens_pct": (45.0, 78.0),
        "precisao_geo_m": (4.0, 12.0),
        "focos_detectados": (40, 180),
        "janela_downlink_min": (20, 70),
    },
    "temperatura_critica": {
        "temp_payload_c": (62.0, 95.0),
        "energia_bateria_pct": (45.0, 75.0),
        "sensor_termico": "degradado",
        "buffer_imagens_pct": (30.0, 70.0),
        "precisao_geo_m": (10.0, 40.0),
        "focos_detectados": (0, 8),
        "janela_downlink_min": (10, 50),
    },
    "energia_baixa": {
        "temp_payload_c": (0.0, 20.0),
        "energia_bateria_pct": (6.0, 18.0),
        "sensor_termico": "degradado",
        "buffer_imagens_pct": (55.0, 95.0),
        "precisao_geo_m": (8.0, 25.0),
        "focos_detectados": (0, 5),
        "janela_downlink_min": (40, 120),
    },
    "perda_comunicacao": {
        "temp_payload_c": (-5.0, 22.0),
        "energia_bateria_pct": (35.0, 70.0),
        "sensor_termico": "offline",
        "buffer_imagens_pct": (88.0, 100.0),
        "precisao_geo_m": (35.0, 120.0),
        "focos_detectados": (0, 2),
        "janela_downlink_min": (90, 240),
    },
}


def _faixa(intervalo: tuple[float, float], casas: int = 1) -> float:
    """Sorteia um valor float dentro de um intervalo."""
    return round(random.uniform(*intervalo), casas)


def _faixa_int(intervalo: tuple[int, int]) -> int:
    """Sorteia um valor inteiro dentro de um intervalo."""
    return random.randint(*intervalo)


def coletar(cenario: str | None = None) -> dict:
    """Coleta um snapshot de telemetria do satelite EnviroSat.

    Args:
        cenario: nome de um cenario em CENARIOS. Se None, sorteia um cenario
                 ponderado (a maior parte do tempo a missao opera normal).

    Returns:
        Dicionario com os parametros monitorados e metadados do ciclo.
    """
    if cenario is None:
        cenario = random.choices(
            population=list(CENARIOS.keys()),
            weights=[55, 15, 10, 10, 10],
            k=1,
        )[0]

    base = CENARIOS.get(cenario, CENARIOS["normal"])

    dados = {
        "cenario": cenario,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "satelite": "EnviroSat-1 (simulado)",
        "orbita": "LEO heliossincrona ~ 628 km",
        "temp_payload_c": _faixa(base["temp_payload_c"]),
        "energia_bateria_pct": _faixa(base["energia_bateria_pct"]),
        "sensor_termico": base["sensor_termico"],
        "buffer_imagens_pct": _faixa(base["buffer_imagens_pct"]),
        "precisao_geo_m": _faixa(base["precisao_geo_m"]),
        "focos_detectados": _faixa_int(base["focos_detectados"]),
        "janela_downlink_min": _faixa_int(base["janela_downlink_min"]),
    }
    return dados


def carregar_cenario_json(nome: str, caminho: str = "data/cenarios.json") -> dict | None:
    """Le um cenario pre-definido de data/cenarios.json (opcional).

    Permite reproduzir exatamente os mesmos dados em demonstracoes e no video.
    """
    path = Path(caminho)
    if not path.exists():
        return None
    try:
        cenarios = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return cenarios.get(nome)


def formatar_legivel(dados: dict) -> str:
    """Formata o snapshot de telemetria em texto legivel para o terminal."""
    return (
        f"Satelite : {dados['satelite']}  |  Orbita: {dados['orbita']}\n"
        f"Coleta   : {dados['timestamp_utc']}  |  Cenario: {dados['cenario']}\n"
        f"---------------------------------------------------------------\n"
        f"  Temp. payload .............. {dados['temp_payload_c']:>7.1f} C\n"
        f"  Energia bateria ............ {dados['energia_bateria_pct']:>7.1f} %\n"
        f"  Sensor termico ............. {dados['sensor_termico']:>9}\n"
        f"  Buffer de imagens .......... {dados['buffer_imagens_pct']:>7.1f} %\n"
        f"  Precisao geolocalizacao .... {dados['precisao_geo_m']:>7.1f} m\n"
        f"  Focos termicos detectados .. {dados['focos_detectados']:>7} pontos\n"
        f"  Proxima janela downlink .... {dados['janela_downlink_min']:>7} min"
    )
