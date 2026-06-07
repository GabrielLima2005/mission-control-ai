"""Gerador de banner ASCII art da Mission Control AI (EnviroSat).

Script auxiliar standalone para experimentar fontes e customizar o banner.

Uso:
    python banner_ascii.py                         # banner padrao
    python banner_ascii.py --fonts                 # lista as 570+ fontes
    python banner_ascii.py --font slant --text "X" # testa fonte/texto
    python banner_ascii.py --demo                  # 8 fontes lado a lado
"""
import sys

import pyfiglet
from rich.console import Console
from rich.align import Align
from rich.text import Text

console = Console()

# Paleta de cores do projeto (estilo Claude Code)
ROXO = "bold #A855F7"
CIANO = "bold #06B6D4"
VERDE = "bold #22C55E"
CINZA = "italic #8484A0"


def banner_padrao() -> None:
    """Exibe o banner oficial em duas linhas, pintado e centralizado."""
    linha1 = pyfiglet.figlet_format("Global Solution", font="ansi_shadow")
    linha2 = pyfiglet.figlet_format("EnviroSat AI", font="ansi_shadow")
    console.print(Align.center(Text(linha1, style=ROXO)))
    console.print(Align.center(Text(linha2, style=VERDE)))
    console.print(
        Align.center(
            Text(
                " -- 2026.1 . Prompt Engineering and AI . FIAP . Trilha EnviroSat -- ",
                style=CINZA,
            )
        )
    )


def listar_fontes() -> None:
    """Lista todas as fontes disponiveis no PyFiglet."""
    for fonte in sorted(pyfiglet.FigletFont.getFonts()):
        console.print(fonte)


def testar_fonte(fonte: str, texto: str) -> None:
    """Renderiza um texto em uma fonte especifica."""
    try:
        arte = pyfiglet.figlet_format(texto, font=fonte)
    except pyfiglet.FontNotFound:
        console.print(f"[red]Fonte '{fonte}' nao encontrada.[/red]")
        return
    console.print(Text(arte, style=CIANO))


def demo() -> None:
    """Demonstra 8 fontes diferentes para o mesmo texto."""
    fontes = [
        "ansi_shadow", "slant", "standard", "big",
        "small", "banner3", "doom", "isometric1",
    ]
    for fonte in fontes:
        console.rule(f"[bold]{fonte}")
        testar_fonte(fonte, "EnviroSat")


def main(argv: list[str]) -> None:
    if "--fonts" in argv:
        listar_fontes()
    elif "--demo" in argv:
        demo()
    elif "--font" in argv:
        i = argv.index("--font")
        fonte = argv[i + 1] if i + 1 < len(argv) else "standard"
        texto = "Mission Control AI"
        if "--text" in argv:
            j = argv.index("--text")
            texto = argv[j + 1] if j + 1 < len(argv) else texto
        testar_fonte(fonte, texto)
    else:
        banner_padrao()


if __name__ == "__main__":
    main(sys.argv[1:])
