"""Lição 13 - Música Real: Corpus e Análise."""

import sys
from pathlib import Path

# Script solto, não faz parte de um pacote instalado: precisa colocar a raiz
# do repo no sys.path antes de importar curso_music21/reaper_bridge.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from music21 import corpus, stream as m21stream  # noqa: E402

from reaper_bridge.connection import get_project  # noqa: E402
from reaper_bridge.errors import ReaperBridgeError  # noqa: E402
from reaper_bridge.midi import write_score_to_tracks  # noqa: E402

TRACK_PREFIX = "Curso 13 - "
CORAL = "bach/bwv66.6"


def build_excerto() -> m21stream.Score:
    """Carrega o coral BWV 66.6 de Bach do corpus embutido do music21 e
    recorta os dois primeiros compassos (a primeira frase)."""
    partitura = corpus.parse(CORAL)
    return partitura.measures(1, 2)


def build_tonalidade_detectada() -> str:
    """Usa a análise automática de tonalidade do music21 sobre o trecho
    -- confirma que é Lá maior sem precisar informar a tonalidade."""
    excerto = build_excerto()
    tonalidade = excerto.analyze("key")
    return f"{tonalidade.tonic.name} {tonalidade.mode}"


def build_total_corais_bach() -> int:
    """Conta quantos corais de Bach existem no corpus embutido do
    music21 -- mostra que há muito mais pra explorar além dessa peça."""
    return len(corpus.search("bach", field="composer"))


def main() -> None:
    excerto = build_excerto()
    tonalidade = build_tonalidade_detectada()
    total_corais = build_total_corais_bach()
    try:
        project = get_project()
        write_score_to_tracks(project, excerto, track_prefix=TRACK_PREFIX)
    except ReaperBridgeError as exc:
        print(f"Não consegui falar com o REAPER: {exc}")
        print(
            "Abra o REAPER e confirme que o reapy está configurado "
            "(reapy.configure_reaper(), rodado a partir do repo principal) "
            "antes de tentar de novo."
        )
        return
    print(
        f"Confira as faixas '{TRACK_PREFIX}Soprano', '{TRACK_PREFIX}Alto', "
        f"'{TRACK_PREFIX}Tenor' e '{TRACK_PREFIX}Bass' no piano roll do REAPER."
    )
    print(f"Tonalidade detectada automaticamente: {tonalidade}.")
    print(
        f"Esse coral é um entre pelo menos {total_corais} corais de Bach "
        "disponíveis no corpus do music21 -- experimente trocar CORAL por "
        "outro (ex: 'bach/bwv1.6') para explorar mais."
    )


if __name__ == "__main__":
    main()
