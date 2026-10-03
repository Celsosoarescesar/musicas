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

# Rodando como `python scripts/caelum_gerar.py`, o Python so poe scripts/ no
# caminho de imports; a raiz do repo (onde moram ace_step/ e caelum/) fica de fora.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from caelum.faixa import FaixaError
from caelum.gerar import gerar, resolve_faixa_dir


def main():
    parser = argparse.ArgumentParser(
        description="Gera uma faixa do album Caelum (ACE-Step + Demucs no Kaggle) em <faixa>/saida/."
    )
    parser.add_argument("faixa", help="Slug da faixa (ex.: 01_semente) ou caminho da pasta")
    parser.add_argument("--seed", type=int, default=None, help="Sobrescreve a seed do faixa.toml")
    parser.add_argument(
        "--instrumental",
        action="store_true",
        help="Plano B: gera a base sem vocal (manda [Instrumental] no lugar da letra)",
    )
    parser.add_argument("--timeout", type=float, default=2700.0)
    args = parser.parse_args()

    load_dotenv()

    try:
        faixa_dir = resolve_faixa_dir(args.faixa)
        song_id, status, detail = gerar(
            faixa_dir, seed=args.seed, instrumental=args.instrumental, timeout=args.timeout
        )
    except FaixaError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)

    if status == "error":
        print(f"Erro (musica #{song_id}): {detail}", file=sys.stderr)
        sys.exit(1)
    print(f"Musica #{song_id} pronta: {detail}")
    print(f"Stems em: {faixa_dir / 'saida'}")


if __name__ == "__main__":
    main()
