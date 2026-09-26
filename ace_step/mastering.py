"""Loudness normalization ("mastering") for generated songs.

O ACE-Step ja devolve uma faixa estereo pronta e mixada -- "masterizar"
aqui significa so normalizar o loudness integrado pra um alvo em LUFS,
com pyloudnorm (matematica pura de DSP, sem GPU). Ver
docs/superpowers/specs/2026-09-13-ace-step-orchestrator-design.md.
"""

from pathlib import Path

import pyloudnorm as pyln
import soundfile as sf


def normalize_loudness(
    input_path: Path, output_path: Path, target_lufs: float = -9.0
) -> None:
    """Read input_path, normalize its integrated loudness to target_lufs, write output_path."""
    data, sample_rate = sf.read(str(input_path))
    meter = pyln.Meter(sample_rate)
    current_loudness = meter.integrated_loudness(data)
    normalized = pyln.normalize.loudness(data, current_loudness, target_lufs)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), normalized, sample_rate, subtype="PCM_16")
