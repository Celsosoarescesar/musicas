import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from ace_step import orchestrator, song_db

DEFAULT_DB_PATH = Path("ace_step/output/songs.db")
DEFAULT_OUTPUT_DIR = Path("ace_step/output")


def main():
    parser = argparse.ArgumentParser(
        description="Cria uma musica: letra via Claude + geracao+separacao via kernel batch no Kaggle."
    )
    parser.add_argument("--prompt", required=True, help="Descricao de estilo/mood da musica")
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bpm", type=int, default=None)
    parser.add_argument("--keyscale", default=None)
    parser.add_argument("--vocal-language", default="en")
    parser.add_argument("--lufs-target", type=float, default=-9.0)
    parser.add_argument("--lyrics", default=None, help="Letra pronta -- pula a geracao via Claude")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--timeout",
        type=float,
        default=2700.0,
        help=(
            "Orcamento total (segundos) para o kernel batch terminar (setup + "
            "geracao + separacao) -- cada musica paga o custo de setup do zero, "
            "aumente para musicas mais longas ou kernels lentos pra iniciar"
        ),
    )
    args = parser.parse_args()

    load_dotenv()

    song_id = song_db.create_song(
        args.db,
        prompt=args.prompt,
        duration=args.duration,
        seed=args.seed,
        bpm=args.bpm,
        keyscale=args.keyscale,
        vocal_language=args.vocal_language,
    )
    print(f"Musica #{song_id} criada (draft).")

    status, detail = orchestrator.run_generation(
        args.db,
        DEFAULT_OUTPUT_DIR,
        song_id,
        prompt=args.prompt,
        duration=args.duration,
        seed=args.seed,
        bpm=args.bpm,
        keyscale=args.keyscale,
        vocal_language=args.vocal_language,
        lufs_target=args.lufs_target,
        lyrics=args.lyrics,
        timeout=args.timeout,
    )

    if status == "error":
        print(f"Erro: {detail}", file=sys.stderr)
        sys.exit(1)
    print(f"Musica #{song_id} pronta: {detail}")


if __name__ == "__main__":
    main()
