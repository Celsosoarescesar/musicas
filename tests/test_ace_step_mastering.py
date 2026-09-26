"""Unit tests for kagglelab.song_mastering."""

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from ace_step import mastering as song_mastering


def test_normalize_loudness_reaches_target_within_half_lu(tmp_path):
    sample_rate = 48000
    duration_s = 2
    t = np.linspace(0, duration_s, sample_rate * duration_s, endpoint=False)
    # Quiet sine wave, stereo -- something normalize_loudness has to boost.
    tone = 0.01 * np.sin(2 * np.pi * 440 * t)
    stereo = np.column_stack([tone, tone])
    input_path = tmp_path / "input.wav"
    sf.write(str(input_path), stereo, sample_rate)

    output_path = tmp_path / "output.wav"
    song_mastering.normalize_loudness(input_path, output_path, target_lufs=-9.0)

    result_data, result_rate = sf.read(str(output_path))
    meter = pyln.Meter(result_rate)
    result_loudness = meter.integrated_loudness(result_data)
    assert abs(result_loudness - (-9.0)) < 0.5


def test_normalize_loudness_writes_pcm16_stereo(tmp_path):
    sample_rate = 48000
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    tone = 0.05 * np.sin(2 * np.pi * 440 * t)
    stereo = np.column_stack([tone, tone])
    input_path = tmp_path / "input.wav"
    sf.write(str(input_path), stereo, sample_rate)

    output_path = tmp_path / "output.wav"
    song_mastering.normalize_loudness(input_path, output_path)

    info = sf.info(str(output_path))
    assert info.channels == 2
    assert info.subtype == "PCM_16"
