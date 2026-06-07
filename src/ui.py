"""Interface CLI estilo Claude Code - usa Rich + prompt-toolkit + PyFiglet.

A camada de apresentacao recebe um `engine` e despacha cada pergunta para
engine.analyze(). Comandos de base: /help, /status, /about, /clear, /exit.
Comando extra da trilha: /cenario <nome> para forcar cenarios de teste.
"""
from __future__ import annotations

from datetime import datetime

import pyfiglet
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
session: PromptSession = PromptSession(
    style=Style.from_dict({"prompt": "#22C55E bold"})
)

CIANO = "#06B6D4"
VERDE = "#22C55E"
ROXO = "#A855F7"
AMARELO = "#FACC15"

CENARIOS_DISPONIVEIS = (
    "normal", "incendio_detectado", "temperatura_critica",
    "energia_baixa", "perda_comunicacao",
)


def show_banner() -> None:
    """Exibe o banner ASCII colorido no inicio."""
    banner = pyfiglet.figlet_format("EnviroSat AI", font="ansi_shadow")
    console.print(Text(banner, style=f"bold {VERDE}"))
    console.print(
        Panel.fit(
            "Bem-vindo a interface da Mission Control AI - Trilha EnviroSat.\n"
            "Monitoramento ambiental e analise por IA generativa.\n"
            "Use /help para ver os comandos . /exit para sair.\n"
            "Modelo: gpt-oss:120b via Ollama Cloud",
            title="[bold]MISSION CONTROL[/bold]",
            subtitle="connected",
            border_style=CIANO,
        )
    )


def show_response(text: str, titulo: str = "Mission Control") -> None:
    """Renderiza a resposta da IA em um painel com timestamp."""
    now = datetime.now().strftime("%H:%M")
    console.print(
        Panel(text, title=f"[bold]{titulo}[/bold]", subtitle=now, border_style=CIANO)
    )


def show_help() -> None:
    """Exibe uma tabela com os comandos disponiveis."""
    tabela = Table(title="Comandos disponiveis", border_style=ROXO, title_style=f"bold {ROXO}")
    tabela.add_column("Comando", style=f"bold {VERDE}")
    tabela.add_column("Descricao")
    tabela.add_row("/help", "Mostra esta ajuda")
    tabela.add_row("/status", "Snapshot atual da telemetria + alertas (sem IA)")
    tabela.add_row("/cenario <nome>", "Forca um cenario de teste e pede analise da IA")
    tabela.add_row("/about", "Sobre o projeto e a missao")
    tabela.add_row("/clear", "Limpa a tela")
    tabela.add_row("/exit", "Encerra a CLI")
    console.print(tabela)
    console.print(
        Text("  Cenarios: " + ", ".join(CENARIOS_DISPONIVEIS), style=AMARELO)
    )
    console.print(
        Text(
            '  Exemplos: "Como esta a missao?"  |  '
            '"/cenario incendio_detectado Resuma a situacao"',
            style="italic #8484A0",
        )
    )


def show_about() -> None:
    """Exibe informacoes sobre o projeto."""
    show_response(
        "EnviroSat-1 (simulado) - satelite de observacao ambiental em orbita LEO\n"
        "heliossincrona, inspirado no Amazonia-1 e Landsat.\n\n"
        "Persona atendida: operador do centro de controle ambiental (INPE / orgao\n"
        "estadual). Impacto terrestre: combate ao desmatamento, resposta rapida a\n"
        "incendios e monitoramento de areas protegidas.\n\n"
        "Stack: Python 3.10+ . Ollama Cloud (gpt-oss:120b) . Rich . prompt-toolkit.\n"
        "FIAP - Global Solution 2026.1 - Prompt Engineering and AI.",
        titulo="Sobre o projeto",
    )


def run_cli(engine) -> None:
    """Loop principal da CLI."""
    show_banner()

    if not engine.is_ready():
        console.print(
            "  [!] Engine status: AGUARDANDO IMPLEMENTACAO [X]\n", style="yellow"
        )
    elif not engine.tem_credencial():
        console.print(
            "  [!] Engine pronto, mas OLLAMA_API_KEY ausente no .env - a IA fica\n"
            "      indisponivel; os comandos deterministicos (/status) seguem ok.\n",
            style="yellow",
        )
    else:
        console.print("  [ok] Engine status: OPERACIONAL\n", style=VERDE)

    while True:
        try:
            user_input = session.prompt(" > ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input == "/exit":
            console.print("Encerrando Mission Control. Boa missao!", style=CIANO)
            break
        if user_input == "/help":
            show_help()
            continue
        if user_input == "/about":
            show_about()
            continue
        if user_input == "/status":
            with console.status("[bold]Coletando telemetria...", spinner="dots"):
                snapshot = engine.status_snapshot()
            show_response(snapshot, titulo="Status da missao")
            continue
        if user_input == "/clear":
            console.clear()
            show_banner()
            continue

        # Qualquer outra entrada (incluindo /cenario ...) vai para o motor.
        with console.status("[bold]Analisando telemetria com a IA...", spinner="earth"):
            resposta = engine.analyze(user_input)
        show_response(resposta)
