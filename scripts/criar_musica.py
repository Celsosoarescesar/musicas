import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ace_step import orchestrator, song_db

DEFAULT_DB_PATH = Path("ace_step/output/songs.db")
DEFAULT_OUTPUT_DIR = Path("ace_step/output")


def main():
    parser = argparse.ArgumentParser(
        description="Cria uma musica: letra via Claude + geracao via ACE-Step (Fase 1) + masterizacao."
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
        default=300.0,
        help="Orcamento total (segundos) para a geracao assincrona (release_task + poll) -- aumente para musicas mais longas",
    )
    args = parser.parse_args()

    load_dotenv()
    base_url = os.environ.get("ACE_STEP_API_URL")
    api_key = os.environ.get("ACE_STEP_API_KEY")
    if not base_url or not api_key:
        print("ACE_STEP_API_URL e/ou ACE_STEP_API_KEY nao encontrados no .env.", file=sys.stderr)
        sys.exit(1)

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
        base_url=base_url,
        api_key=api_key,
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
