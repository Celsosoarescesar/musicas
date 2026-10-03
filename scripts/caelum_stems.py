import os
import subprocess
import sys

if not sys.flags.utf8_mode:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    result = subprocess.run([sys.executable, __file__, *sys.argv[1:]], env=env)
    sys.exit(result.returncode)

import argparse
from pathlib import Path

# Rodando como `python scripts/caelum_stems.py`, a raiz do repo fica fora do sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from caelum.faixa import FaixaError
from caelum.gerar import resolve_faixa_dir
from caelum.stems import StemsError, separar_stems


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Separa os stems (Demucs htdemucs_6s, local) de uma musica ja gerada "
            "pelo caelum_gerar, se voce gostou dela."
        )
    )
    parser.add_argument("faixa", help="Slug da faixa (ex.: 01_quebra_de_fe) ou caminho da pasta")
    parser.add_argument("song_id", type=int, help="Id da musica (o numero em <id>_master.wav)")
    args = parser.parse_args()

    try:
        faixa_dir = resolve_faixa_dir(args.faixa)
        print("Separando stems (na CPU pode levar varios minutos)...")
        stems = separar_stems(faixa_dir, args.song_id)
    except (FaixaError, StemsError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Stems prontos em {faixa_dir / 'saida'}:")
    for name, path in stems.items():
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
