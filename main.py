"""Mission Control AI - ponto de entrada do sistema.

Trilha: EnviroSat (Observacao Ambiental).
Instancia o motor de analise (MissionEngine) e entrega o controle para a UI.
A logica de dominio fica em src/engine.py, src/telemetria.py e src/alertas.py.
"""
from src.ui import run_cli
from src.engine import MissionEngine

if __name__ == "__main__":
    engine = MissionEngine()
    run_cli(engine)
