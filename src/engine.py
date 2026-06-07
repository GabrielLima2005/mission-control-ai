"""Motor de analise da Mission Control AI - Trilha EnviroSat.

Combina:
  (a) a funcao llm() - ponto unico de contato com o modelo gpt-oss:120b;
  (b) a classe MissionEngine - orquestra telemetria + alertas + IA.

Fluxo do analyze():
  1. Coleta telemetria (src.telemetria.coletar)
  2. Avalia alertas/decisao em Python (src.alertas.avaliar)
  3. Aciona respostas automaticas (src.alertas.responder_automatico)
  4. Monta o prompt com os dados REAIS injetados dinamicamente
  5. Chama llm(prompt, system=system_prompt)
  6. Retorna a analise contextualizada
"""
from __future__ import annotations

import os
from collections import deque
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client

from src import alertas, telemetria

load_dotenv()

# Identificacao da trilha escolhida pelo grupo.
TRILHA = "envirosat"  # "agrosat" | "envirosat" | "connectsat" | "mobilitysat"

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")},
)


def llm(prompt: str, system: str | None = None, max_tokens: int = 800,
        temperature: float = 0.3) -> str:
    """Envia prompt ao gpt-oss:120b via Ollama Cloud. Ponto unico de integracao."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        return client.chat(
            model="gpt-oss:120b",
            messages=messages,
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001 - queremos exibir qualquer erro de rede/API
        return f"  [!] Erro ao consultar IA: {e}"


def load_system_prompt() -> str:
    """Le o system prompt de prompts/system_prompt.md."""
    path = Path("prompts/system_prompt.md")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Voce e um assistente de operacoes de satelite."  # fallback


class MissionEngine:
    """Motor de analise da missao EnviroSat."""

    def __init__(self) -> None:
        self.trilha = TRILHA
        self.system_prompt = load_system_prompt()
        # Memoria de contexto: ultimos ciclos para dar consciencia temporal a IA.
        self.historico: deque[dict] = deque(maxlen=5)

    def is_ready(self) -> bool:
        """O motor esta implementado e pronto para operar."""
        return True

    def tem_credencial(self) -> bool:
        """Indica se a OLLAMA_API_KEY foi carregada do .env."""
        return bool(os.environ.get("OLLAMA_API_KEY"))

    def _coletar_ciclo(self, cenario: str | None = None) -> dict:
        """Coleta um ciclo completo: telemetria + avaliacao + acoes automaticas."""
        dados = telemetria.coletar(cenario)
        avaliacao = alertas.avaliar(dados)
        acoes = alertas.responder_automatico(dados, avaliacao)
        ciclo = {"dados": dados, "avaliacao": avaliacao, "acoes": acoes}
        self.historico.append(ciclo)
        return ciclo

    def _resumo_historico(self) -> str:
        """Resume os ciclos anteriores para injetar consciencia temporal."""
        if len(self.historico) <= 1:
            return "Sem ciclos anteriores registrados."
        linhas = []
        for i, ciclo in enumerate(list(self.historico)[:-1], start=1):
            d = ciclo["dados"]
            linhas.append(
                f"  Ciclo {i}: severidade={ciclo['avaliacao']['severidade_geral']}, "
                f"temp={d['temp_payload_c']:.1f}C, energia={d['energia_bateria_pct']:.1f}%, "
                f"focos={d['focos_detectados']}"
            )
        return "\n".join(linhas)

    def _montar_prompt(self, pergunta: str, ciclo: dict) -> str:
        """Monta o prompt do usuario com os dados REAIS injetados dinamicamente."""
        dados = ciclo["dados"]
        avaliacao = ciclo["avaliacao"]
        acoes = ciclo["acoes"]

        bloco_alertas = (
            alertas.formatar_alertas(avaliacao)
            if avaliacao["alertas"]
            else "  Nenhum alerta ativo."
        )
        bloco_acoes = "\n".join(f"  - {a}" for a in acoes)

        return (
            "=== TELEMETRIA ATUAL (EnviroSat-1) ===\n"
            f"{telemetria.formatar_legivel(dados)}\n\n"
            f"=== SEVERIDADE GERAL (calculada em Python): {avaliacao['severidade_geral']} ===\n"
            "=== ALERTAS ATIVOS ===\n"
            f"{bloco_alertas}\n\n"
            "=== ACOES AUTOMATICAS JA EXECUTADAS PELO SISTEMA DE BORDO ===\n"
            f"{bloco_acoes}\n\n"
            "=== HISTORICO RECENTE (ciclos anteriores) ===\n"
            f"{self._resumo_historico()}\n\n"
            "=== PERGUNTA DO OPERADOR ===\n"
            f"{pergunta}\n\n"
            "Responda seguindo EXATAMENTE o formato definido no system prompt "
            "(Diagnostico tecnico / Impacto terrestre / Recomendacao ao operador)."
        )

    def status_snapshot(self) -> str:
        """Retorna um resumo legivel do estado atual da telemetria (sem IA)."""
        ciclo = self._coletar_ciclo()
        dados = ciclo["dados"]
        avaliacao = ciclo["avaliacao"]
        return (
            f"{telemetria.formatar_legivel(dados)}\n"
            f"---------------------------------------------------------------\n"
            f"  Severidade geral: {avaliacao['severidade_geral']}\n\n"
            f"{alertas.formatar_alertas(avaliacao)}\n"
            f"---------------------------------------------------------------\n"
            f"  Acoes automaticas:\n"
            + "\n".join(f"    - {a}" for a in ciclo["acoes"])
        )

    def analyze(self, pergunta_usuario: str) -> str:
        """Analisa a pergunta com base na telemetria + alertas + IA."""
        # Permite forcar um cenario: ex. "/cenario incendio_detectado Como estamos?"
        cenario = None
        pergunta = pergunta_usuario
        if pergunta_usuario.startswith("/cenario"):
            partes = pergunta_usuario.split(maxsplit=2)
            if len(partes) >= 2 and partes[1] in telemetria.CENARIOS:
                cenario = partes[1]
                pergunta = partes[2] if len(partes) == 3 else "Como esta a missao?"

        ciclo = self._coletar_ciclo(cenario)

        if not self.tem_credencial():
            return (
                "  [!] OLLAMA_API_KEY nao encontrada no .env - exibindo apenas a\n"
                "      camada deterministica (telemetria + alertas), sem analise da IA.\n\n"
                + self.status_snapshot()
            )

        prompt = self._montar_prompt(pergunta, ciclo)
        resposta_ia = llm(prompt, system=self.system_prompt)

        cabecalho = (
            f"Cenario: {ciclo['dados']['cenario']}  |  "
            f"Severidade: {ciclo['avaliacao']['severidade_geral']}\n"
            f"---------------------------------------------------------------\n"
        )
        return cabecalho + resposta_ia
