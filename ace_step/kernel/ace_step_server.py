"""ACE-Step 1.5 music generation API — runs as a Kaggle kernel (GPU).

Roda dentro de um Kaggle Kernel, nao localmente (sem GPU local). Ver
docs/superpowers/specs/2026-09-19-ace-step-native-package-design.md para o
desenho completo (por que este script clona e roda o pacote `acestep`
nativo em vez de carregar o modelo direto via `diffusers`).

Ao contrario dos outros kernels deste repo, este fica rodando
indefinidamente como servidor (o servidor REST do pacote `acestep` +
tunel ngrok num dominio fixo), ate o Kaggle encerrar a sessao.

As funcoes abaixo (antes de main()) nao tem nenhum import de terceiros de
proposito: elas sao a unica parte deste arquivo testavel localmente (sem
GPU, sem o pacote `acestep`/pyngrok instalados). Tudo que precisa dessas
bibliotecas pesadas fica dentro de main(), com os imports feitos la dentro
(lazy) -- assim, importar este arquivo (via importlib, nos testes) nao
executa o git clone/pip install nem exige essas libs localmente.
"""

import base64
import json
from pathlib import Path


_ACESTEP_REPO_URL = "https://github.com/ace-step/ACE-Step-1.5.git"
# Pinned (not tracking `main`) for reproducibility: the dtype patch and the
# flash-attn requirements.txt filter below are both matched against this
# exact commit's file contents (confirmed live -- an upstream reword of
# either file would silently break the string match). To pick up a future
# upstream fix, re-run `git ls-remote https://github.com/ace-step/ACE-Step-1.5.git HEAD`
# and update this constant (and re-verify the patches still match).
_ACESTEP_REPO_COMMIT = "ca1e85fe9430179831e6bc6be790c332190a3866"
# Not the XL (4B) turbo variant: confirmed live, `acestep-v15-xl-turbo` is
# a separate, additional download beyond the package's "core" bundle
# (INSTALL.md: "~10GB for core models", the main `Ace-Step1.5` download
# already includes the plain, non-XL `acestep-v15-turbo`) and its checkpoint
# alone filled the rest of /kaggle/working's disk mid-download
# (`OSError: [Errno 28] No space left on device`), even after --no-cache-dir
# freed up what pip's wheel cache was using. The non-XL turbo model is the
# package's own default (see `/v1/models`'s `is_default: true` in
# docs/en/API.md) and fits the disk budget the core download already
# accounts for.
_ACESTEP_MODEL_CONFIG = "acestep-v15-turbo"
_SECRETS_DATASET_REF = "celsosoarescesar/daw-music-studio-secrets"
# _PROXY_PORT is the port ngrok tunnels (unchanged value from before this
# split -- the public URL/contract doesn't change). acestep.api_server
# itself now runs on _ACESTEP_PORT, an internal-only port that proxy_server.py
# (this folder) forwards the existing endpoints to. See
# docs/superpowers/specs/2026-09-19-demucs-kernel-proxy-design.md.
_PROXY_PORT = 8188
_ACESTEP_PORT = 8189
# The native `acestep` package (github.com/ace-step/ACE-Step-1.5) replaces
# the diffusers-based server this file used to run directly. Confirmed live
# this session: diffusers' AceStepTransformer1DModel forward pass isn't
# multi-GPU-safe (accelerate's device_map sharding produced "tensors on two
# devices" errors -- an architecture-level incompatibility, not a config
# problem), so splitting the model across the kernel's 2 T4s was a dead
# end. The acestep package's own GPU_COMPATIBILITY.md documents up to
# 8-10 minutes of audio on a single 16-20GB GPU (a T4) via its own
# automatic INT8 quantization + CPU offload -- no multi-GPU needed for a
# 4-minute (240s) song.


def resolve_secrets_dataset_dir(kaggle_input_dir: Path, dataset_ref: str) -> Path:
    """Return whichever known Kaggle input-mount layout actually holds the secrets dataset.

    `dataset_ref` is the `owner/slug` string from kernel-metadata.json's
    `dataset_sources`. Kaggle has mounted a kernel's `dataset_sources` at
    `input/<slug>` (the documented, typical layout) but a nested
    `input/datasets/<owner>/<slug>` has also been observed live for this same
    dataset -- try the flat layout first, fall back to the nested one, and
    fall through to the flat path (letting `load_secrets` raise its own clear
    error) if neither actually has a `secrets.json`.
    """
    owner, _, slug = dataset_ref.partition("/")
    flat = Path(kaggle_input_dir) / slug
    if (flat / "secrets.json").exists():
        return flat
    nested = Path(kaggle_input_dir) / "datasets" / owner / slug
    if (nested / "secrets.json").exists():
        return nested
    return flat


def load_secrets(dataset_dir: Path) -> dict:
    """Load the kernel's secrets from a `secrets.json` file in a mounted Kaggle dataset.

    Works around a known Kaggle platform limitation, confirmed live: secrets
    attached through the web UI's Secrets panel do not carry over to kernels
    pushed via the API (`kaggle kernels push`) -- `kaggle_secrets.
    UserSecretsClient().get_secret(...)` fails with a ConnectionError in that
    case, even when the secret shows as attached in the UI. The workaround
    (Kaggle's own recommended pattern for this exact problem) is to store
    secrets in a private dataset instead and read them from its mounted path.
    """
    secrets_path = Path(dataset_dir) / "secrets.json"
    try:
        with open(secrets_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Dataset de secrets nao encontrado em {secrets_path} -- confira "
            "'dataset_sources' em kernel-metadata.json"
        ) from exc


def validate_secrets(secrets: dict, required_keys: list[str]) -> None:
    """Raise ValueError if any of `required_keys` is missing or empty in `secrets`."""
    missing = [key for key in required_keys if not secrets.get(key)]
    if missing:
        raise ValueError(
            f"Secrets ausentes ou vazios no dataset de secrets: {', '.join(missing)}"
        )


def first_dead_process(processes: dict[str, object]) -> str | None:
    """Return the name of the first process (by dict iteration order) whose
    `.poll()` already returned an exit code, or None if all are alive.

    Duck-typed on `.poll()` (the same method `subprocess.Popen` exposes)
    so this is testable with plain fake objects -- no real subprocess
    needed.
    """
    for name, process in processes.items():
        if process.poll() is not None:
            return name
    return None


# Kaggle's `script`-type kernel push (kernel-metadata.json's kernel_type)
# only stores the single `code_file` -- confirmed live: `proxy_server.py`
# never reached the kernel even though it sits next to this file locally,
# so `Path(__file__).parent / "proxy_server.py"` pointed at a path that
# never existed at runtime, the proxy subprocess died with
# FileNotFoundError, and first_dead_process's guard took the whole kernel
# down. proxy_server.py's exact bytes are embedded below (base64, so no
# quoting/escaping hazards) and written to disk at runtime instead.
#
# Regenerate this constant whenever projects/ace-step-api/kernel/proxy_server.py
# changes -- tests/test_ace_step_server.py's
# test_write_proxy_server_script_matches_repo_file decodes it and diffs it
# against the real file, so a stale copy fails locally instead of on a live
# kernel:
#
#   python -c "
#   import base64, textwrap
#   data = open('projects/ace-step-api/kernel/proxy_server.py', 'rb').read()
#   b64 = base64.b64encode(data).decode('ascii')
#   print('_PROXY_SERVER_SOURCE_B64 = (')
#   for line in textwrap.wrap(b64, 76):
#       print(f'    \"{line}\"')
#   print(')')
#   "
_PROXY_SERVER_SOURCE_B64 = (
    "IiIiUmV2ZXJzZS1wcm94eSArIHN0ZW0tc2VwYXJhdGlvbiBzZXJ2ZXIgZm9yIHRoZSBhY2Utc3Rl"
    "cC1hcGkgS2FnZ2xlIGtlcm5lbC4NCg0KUnVucyBhcyBhIHNlY29uZCBzdWJwcm9jZXNzIGFsb25n"
    "c2lkZSBhY2VzdGVwLmFwaV9zZXJ2ZXIgKHNlZQ0KYWNlX3N0ZXBfc2VydmVyLnB5IGluIHRoaXMg"
    "c2FtZSBmb2xkZXIpLCBvbiB0aGUgcG9ydCBuZ3JvayBhY3R1YWxseQ0KdHVubmVscy4gTm8gaGVh"
    "dnkgaW1wb3J0cyBhdCBtb2R1bGUgbGV2ZWwgKG5vIHRvcmNoLCBubyBkZW11Y3MpIC0tDQpmYXN0"
    "YXBpL2h0dHB4L3V2aWNvcm4gYXJlIGFscmVhZHkgdGhpcyByZXBvJ3Mgb3duIHByb2plY3QgZGVw"
    "ZW5kZW5jaWVzDQoodXNlZCBieSB0aGUgbXVzaWMtc3R1ZGlvIGJhY2tlbmQpLCBzbyB0aGlzIHdo"
    "b2xlIGZpbGUgaXMgdGVzdGFibGUNCmxvY2FsbHkgd2l0aG91dCBhIEdQVSBvciB0aGUgYGRlbXVj"
    "c2AgcGFja2FnZSBpbnN0YWxsZWQuIFNlZQ0KZG9jcy9zdXBlcnBvd2Vycy9zcGVjcy8yMDI2LTA5"
    "LTE5LWRlbXVjcy1rZXJuZWwtcHJveHktZGVzaWduLm1kLg0KIiIiDQoNCmltcG9ydCBqc29uDQpp"
    "bXBvcnQgc3VicHJvY2Vzcw0KaW1wb3J0IHN5cw0KaW1wb3J0IHRocmVhZGluZw0KaW1wb3J0IHV1"
    "aWQNCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aA0KZnJvbSB1cmxsaWIucGFyc2UgaW1wb3J0IHBh"
    "cnNlX3FzLCBxdW90ZSwgdW5xdW90ZSwgdXJscGFyc2UNCg0KaW1wb3J0IGh0dHB4DQpmcm9tIGZh"
    "c3RhcGkgaW1wb3J0IEZhc3RBUEksIEhlYWRlciwgSFRUUEV4Y2VwdGlvbiwgUmVxdWVzdA0KZnJv"
    "bSBmYXN0YXBpLnJlc3BvbnNlcyBpbXBvcnQgRmlsZVJlc3BvbnNlLCBSZXNwb25zZQ0KZnJvbSBw"
    "eWRhbnRpYyBpbXBvcnQgQmFzZU1vZGVsDQoNCg0KZGVmIHBhcnNlX2F1ZGlvX3BhdGgoZmlsZV9y"
    "ZWY6IHN0cikgLT4gc3RyOg0KICAgICIiIkV4dHJhY3QgdGhlIHJhdyBmaWxlc3lzdGVtIHBhdGgg"
    "ZnJvbSBhIGAvdjEvYXVkaW8/cGF0aD0uLi5gLXN0eWxlIHN0cmluZy4NCg0KICAgIGBmaWxlX3Jl"
    "ZmAgaXMgdGhlIHNhbWUgb3BhcXVlIHN0cmluZyBgZ2VuZXJhdGVfbXVzaWNgJ3MgcmVzdWx0DQog"
    "ICAgYWxyZWFkeSByZXR1cm5zIGluIGByZXN1bHRbImZpbGUiXWAgLS0gYSByZWxhdGl2ZSBVUkwg"
    "d2l0aCB0aGUgcmVhbA0KICAgIHBhdGggVVJMLWVuY29kZWQgaW4gaXRzIGBwYXRoYCBxdWVyeSBw"
    "YXJhbWV0ZXIuDQogICAgIiIiDQogICAgcGFyc2VkID0gdXJscGFyc2UoZmlsZV9yZWYpDQogICAg"
    "cXVlcnkgPSBwYXJzZV9xcyhwYXJzZWQucXVlcnkpDQogICAgdHJ5Og0KICAgICAgICBwYXRoX3Zh"
    "bHVlcyA9IHF1ZXJ5WyJwYXRoIl0NCiAgICBleGNlcHQgS2V5RXJyb3IgYXMgZXhjOg0KICAgICAg"
    "ICByYWlzZSBWYWx1ZUVycm9yKA0KICAgICAgICAgICAgZiJOYW8gZm9pIHBvc3NpdmVsIGV4dHJh"
    "aXIgbyBjYW1pbmhvIGRlIHtmaWxlX3JlZiFyfSAtLSBlc3BlcmF2YSB1bSAiDQogICAgICAgICAg"
    "ICAicGFyYW1ldHJvIGRlIHF1ZXJ5ICdwYXRoJyINCiAgICAgICAgKSBmcm9tIGV4Yw0KICAgIHJl"
    "dHVybiB1bnF1b3RlKHBhdGhfdmFsdWVzWzBdKQ0KDQoNCmRlZiBidWlsZF9kZW11Y3NfY29tbWFu"
    "ZCgNCiAgICBpbnB1dF9wYXRoOiBQYXRoLCBvdXRfZGlyOiBQYXRoLCAqLCBtb2RlbDogc3RyID0g"
    "Imh0ZGVtdWNzXzZzIiwgZGV2aWNlOiBzdHIgPSAiY3VkYSINCikgLT4gbGlzdFtzdHJdOg0KICAg"
    "ICIiIkJ1aWxkIHRoZSBgcHl0aG9uIC1tIGRlbXVjc2AgY29tbWFuZCB0byBzZXBhcmF0ZSBgaW5w"
    "dXRfcGF0aGAgaW50byBgb3V0X2RpcmAuIiIiDQogICAgcmV0dXJuIFsNCiAgICAgICAgc3lzLmV4"
    "ZWN1dGFibGUsDQogICAgICAgICItbSIsDQogICAgICAgICJkZW11Y3MiLA0KICAgICAgICAiLW4i"
    "LA0KICAgICAgICBtb2RlbCwNCiAgICAgICAgIi1kIiwNCiAgICAgICAgZGV2aWNlLA0KICAgICAg"
    "ICAiLS1vdXQiLA0KICAgICAgICBzdHIob3V0X2RpciksDQogICAgICAgIHN0cihpbnB1dF9wYXRo"
    "KSwNCiAgICBdDQoNCg0KIyBodGRlbXVjc182cyAobm90IHRoZSA0LXN0ZW0gaHRkZW11Y3MpIC0t"
    "IGFkZHMgZ3VpdGFyIGFuZCBwaWFubyBhcyB0aGVpciBvd24NCiMgc3RlbXMuIFRoaXMgaXMgdGhl"
    "IHByYWN0aWNhbCBjZWlsaW5nIGFtb25nIG1hdHVyZSwgd2lkZWx5LXVzZWQgb3BlbiBtb2RlbHM7"
    "DQojIG5vIHJlbGlhYmxlIG1vZGVsIHNlcGFyYXRlcyBpbmRpdmlkdWFsIGluc3RydW1lbnRzIGJl"
    "eW9uZCB0aGlzIChjb25maXJtZWQNCiMgdmlhIHJlc2VhcmNoIDIwMjYtMDktMjYsIHNlZSBwcm9q"
    "ZWN0IG1lbW9yeSkuDQpfU1RFTV9OQU1FUyA9ICgidm9jYWxzIiwgImRydW1zIiwgImJhc3MiLCAi"
    "Z3VpdGFyIiwgInBpYW5vIiwgIm90aGVyIikNCg0KDQpkZWYgc3RlbXNfZnJvbV9vdXRwdXRfZGly"
    "KG91dF9kaXI6IFBhdGgsIG1vZGVsOiBzdHIsIHRyYWNrX25hbWU6IHN0cikgLT4gZGljdFtzdHIs"
    "IFBhdGhdOg0KICAgICIiIk1hcCBEZW11Y3MnIG91dHB1dCBkaXJlY3RvcnkgbGF5b3V0IHRvIHRo"
    "ZSA2IGV4cGVjdGVkIHN0ZW0gZmlsZSBwYXRocy4NCg0KICAgIERlbXVjcyB3cml0ZXMgdG8NCiAg"
    "ICBgPG91dF9kaXI+Lzxtb2RlbD4vPHRyYWNrX25hbWU+L3t2b2NhbHMsZHJ1bXMsYmFzcyxndWl0"
    "YXIscGlhbm8sb3RoZXJ9LndhdmAuDQogICAgUmFpc2VzIFZhbHVlRXJyb3IgKG5ldmVyIGEgcGFy"
    "dGlhbCBkaWN0KSBpZiBhbnkgZXhwZWN0ZWQgc3RlbSBpcyBtaXNzaW5nLg0KICAgICIiIg0KICAg"
    "IHRyYWNrX2RpciA9IFBhdGgob3V0X2RpcikgLyBtb2RlbCAvIHRyYWNrX25hbWUNCiAgICBzdGVt"
    "cyA9IHtuYW1lOiB0cmFja19kaXIgLyBmIntuYW1lfS53YXYiIGZvciBuYW1lIGluIF9TVEVNX05B"
    "TUVTfQ0KICAgIG1pc3NpbmcgPSBbbmFtZSBmb3IgbmFtZSwgcGF0aCBpbiBzdGVtcy5pdGVtcygp"
    "IGlmIG5vdCBwYXRoLmV4aXN0cygpXQ0KICAgIGlmIG1pc3Npbmc6DQogICAgICAgIGZvdW5kID0g"
    "c29ydGVkKHAubmFtZSBmb3IgcCBpbiB0cmFja19kaXIuZ2xvYigiKiIpKSBpZiB0cmFja19kaXIu"
    "ZXhpc3RzKCkgZWxzZSBbXQ0KICAgICAgICByYWlzZSBWYWx1ZUVycm9yKA0KICAgICAgICAgICAg"
    "ZiJEZW11Y3MgbmFvIGdlcm91IG9zIHN0ZW1zIGVzcGVyYWRvcyBlbSB7dHJhY2tfZGlyfSAtLSBm"
    "YWx0YW5kbzogIg0KICAgICAgICAgICAgZiJ7JywgJy5qb2luKG1pc3NpbmcpfSAoYXJxdWl2b3Mg"
    "ZW5jb250cmFkb3M6IHtmb3VuZH0pIg0KICAgICAgICApDQogICAgcmV0dXJuIHN0ZW1zDQoNCg0K"
    "Y2xhc3MgU2VwYXJhdGVUYXNrUmVxdWVzdChCYXNlTW9kZWwpOg0KICAgIGZpbGU6IHN0cg0KDQoN"
    "CmNsYXNzIFNlcGFyYXRlVGFza1Jlc3BvbnNlKEJhc2VNb2RlbCk6DQogICAgdGFza19pZDogc3Ry"
    "DQoNCg0KY2xhc3MgUXVlcnlUYXNrTGlzdFJlcXVlc3QoQmFzZU1vZGVsKToNCiAgICB0YXNrX2lk"
    "X2xpc3Q6IGxpc3Rbc3RyXQ0KDQoNCmRlZiBfY2hlY2tfYXBpX2tleShhdXRob3JpemF0aW9uOiBz"
    "dHIgfCBOb25lLCBhcGlfa2V5OiBzdHIpIC0+IE5vbmU6DQogICAgaWYgYXV0aG9yaXphdGlvbiAh"
    "PSBmIkJlYXJlciB7YXBpX2tleX0iOg0KICAgICAgICByYWlzZSBIVFRQRXhjZXB0aW9uKDQwMSwg"
    "IkNoYXZlIGRlIEFQSSBpbnZhbGlkYSBvdSBhdXNlbnRlIikNCg0KDQpkZWYgY3JlYXRlX2FwcChh"
    "Y2VzdGVwX2Jhc2VfdXJsOiBzdHIsIGFwaV9rZXk6IHN0cikgLT4gRmFzdEFQSToNCiAgICBhcHAg"
    "PSBGYXN0QVBJKHRpdGxlPSJBQ0UtU3RlcCBwcm94eSArIHN0ZW0gc2VwYXJhdGlvbiIpDQogICAg"
    "dGFza3M6IGRpY3Rbc3RyLCBkaWN0XSA9IHt9DQogICAgdGFza3NfbG9jayA9IHRocmVhZGluZy5M"
    "b2NrKCkNCg0KICAgIGRlZiBfcnVuX3NlcGFyYXRpb24odGFza19pZDogc3RyLCBpbnB1dF9wYXRo"
    "OiBzdHIpIC0+IE5vbmU6DQogICAgICAgIG91dF9kaXIgPSBQYXRoKGlucHV0X3BhdGgpLnBhcmVu"
    "dCAvICJzdGVtcyIgLyB0YXNrX2lkDQogICAgICAgIG91dF9kaXIubWtkaXIocGFyZW50cz1UcnVl"
    "LCBleGlzdF9vaz1UcnVlKQ0KICAgICAgICB0cmFja19uYW1lID0gUGF0aChpbnB1dF9wYXRoKS5z"
    "dGVtDQogICAgICAgIGNvbW1hbmQgPSBidWlsZF9kZW11Y3NfY29tbWFuZChQYXRoKGlucHV0X3Bh"
    "dGgpLCBvdXRfZGlyKQ0KICAgICAgICB0cnk6DQogICAgICAgICAgICBzdWJwcm9jZXNzLnJ1bihj"
    "b21tYW5kLCBjaGVjaz1UcnVlLCBjYXB0dXJlX291dHB1dD1UcnVlLCB0ZXh0PVRydWUpDQogICAg"
    "ICAgICAgICBzdGVtcyA9IHN0ZW1zX2Zyb21fb3V0cHV0X2RpcihvdXRfZGlyLCAiaHRkZW11Y3Nf"
    "NnMiLCB0cmFja19uYW1lKQ0KICAgICAgICAgICAgcmVzdWx0ID0gew0KICAgICAgICAgICAgICAg"
    "IG5hbWU6IGYiL3YxL3N0ZW1zP3BhdGg9e3F1b3RlKHN0cihwYXRoKSwgc2FmZT0nJyl9Ig0KICAg"
    "ICAgICAgICAgICAgIGZvciBuYW1lLCBwYXRoIGluIHN0ZW1zLml0ZW1zKCkNCiAgICAgICAgICAg"
    "IH0NCiAgICAgICAgICAgIHdpdGggdGFza3NfbG9jazoNCiAgICAgICAgICAgICAgICB0YXNrc1t0"
    "YXNrX2lkXSA9IHsic3RhdHVzIjogMSwgInJlc3VsdCI6IGpzb24uZHVtcHMocmVzdWx0KX0NCiAg"
    "ICAgICAgZXhjZXB0IHN1YnByb2Nlc3MuQ2FsbGVkUHJvY2Vzc0Vycm9yIGFzIGV4YzoNCiAgICAg"
    "ICAgICAgICMgU2FtZSAicHJlZmVyIHN0ZGVyciwgZmFsbCBiYWNrIHRvIHN0cihleGMpIiBwYXR0"
    "ZXJuIGFscmVhZHkNCiAgICAgICAgICAgICMgdXNlZCBieSBrYWdnbGVsYWIuc29uZ19seXJpY3Mg"
    "Zm9yIGEgZmFpbGVkIHN1YnByb2Nlc3MgLS0NCiAgICAgICAgICAgICMgc3RyKENhbGxlZFByb2Nl"
    "c3NFcnJvcikgYWxvbmUgZG9lc24ndCBpbmNsdWRlIHN0ZGVyciwgYW5kDQogICAgICAgICAgICAj"
    "IHN0ZGVyciBpcyBleGFjdGx5IHdoZXJlIERlbXVjcyB3b3VsZCByZXBvcnQgZS5nLiBhIENVREEg"
    "T09NLg0KICAgICAgICAgICAgZGV0YWlsID0gKGV4Yy5zdGRlcnIgb3IgIiIpLnN0cmlwKCkgb3Ig"
    "c3RyKGV4YykNCiAgICAgICAgICAgIHdpdGggdGFza3NfbG9jazoNCiAgICAgICAgICAgICAgICB0"
    "YXNrc1t0YXNrX2lkXSA9IHsic3RhdHVzIjogMiwgInJlc3VsdCI6IGRldGFpbH0NCiAgICAgICAg"
    "ZXhjZXB0IEV4Y2VwdGlvbiBhcyBleGM6DQogICAgICAgICAgICB3aXRoIHRhc2tzX2xvY2s6DQog"
    "ICAgICAgICAgICAgICAgdGFza3NbdGFza19pZF0gPSB7InN0YXR1cyI6IDIsICJyZXN1bHQiOiBz"
    "dHIoZXhjKX0NCg0KICAgIEBhcHAucG9zdCgiL3NlcGFyYXRlX3Rhc2siLCByZXNwb25zZV9tb2Rl"
    "bD1TZXBhcmF0ZVRhc2tSZXNwb25zZSkNCiAgICBkZWYgc2VwYXJhdGVfdGFzaygNCiAgICAgICAg"
    "cGF5bG9hZDogU2VwYXJhdGVUYXNrUmVxdWVzdCwgYXV0aG9yaXphdGlvbjogc3RyIHwgTm9uZSA9"
    "IEhlYWRlcihOb25lKQ0KICAgICkgLT4gU2VwYXJhdGVUYXNrUmVzcG9uc2U6DQogICAgICAgIF9j"
    "aGVja19hcGlfa2V5KGF1dGhvcml6YXRpb24sIGFwaV9rZXkpDQogICAgICAgIGlucHV0X3BhdGgg"
    "PSBwYXJzZV9hdWRpb19wYXRoKHBheWxvYWQuZmlsZSkNCiAgICAgICAgdGFza19pZCA9IHN0cih1"
    "dWlkLnV1aWQ0KCkpDQogICAgICAgIHdpdGggdGFza3NfbG9jazoNCiAgICAgICAgICAgIHRhc2tz"
    "W3Rhc2tfaWRdID0geyJzdGF0dXMiOiAwLCAicmVzdWx0IjogTm9uZX0NCiAgICAgICAgdGhyZWFk"
    "ID0gdGhyZWFkaW5nLlRocmVhZCgNCiAgICAgICAgICAgIHRhcmdldD1fcnVuX3NlcGFyYXRpb24s"
    "IGFyZ3M9KHRhc2tfaWQsIGlucHV0X3BhdGgpLCBkYWVtb249VHJ1ZQ0KICAgICAgICApDQogICAg"
    "ICAgIHRocmVhZC5zdGFydCgpDQogICAgICAgIHJldHVybiBTZXBhcmF0ZVRhc2tSZXNwb25zZSh0"
    "YXNrX2lkPXRhc2tfaWQpDQoNCiAgICBAYXBwLnBvc3QoIi9xdWVyeV9zZXBhcmF0aW9uX3Jlc3Vs"
    "dCIpDQogICAgZGVmIHF1ZXJ5X3NlcGFyYXRpb25fcmVzdWx0KA0KICAgICAgICBwYXlsb2FkOiBR"
    "dWVyeVRhc2tMaXN0UmVxdWVzdCwgYXV0aG9yaXphdGlvbjogc3RyIHwgTm9uZSA9IEhlYWRlcihO"
    "b25lKQ0KICAgICkgLT4gbGlzdFtkaWN0XToNCiAgICAgICAgX2NoZWNrX2FwaV9rZXkoYXV0aG9y"
    "aXphdGlvbiwgYXBpX2tleSkNCiAgICAgICAgd2l0aCB0YXNrc19sb2NrOg0KICAgICAgICAgICAg"
    "cmV0dXJuIFsNCiAgICAgICAgICAgICAgICB7InRhc2tfaWQiOiB0YXNrX2lkLCAqKnRhc2tzW3Rh"
    "c2tfaWRdfQ0KICAgICAgICAgICAgICAgIGZvciB0YXNrX2lkIGluIHBheWxvYWQudGFza19pZF9s"
    "aXN0DQogICAgICAgICAgICAgICAgaWYgdGFza19pZCBpbiB0YXNrcw0KICAgICAgICAgICAgXQ0K"
    "DQogICAgQGFwcC5nZXQoIi92MS9zdGVtcyIpDQogICAgZGVmIGdldF9zdGVtKHBhdGg6IHN0ciwg"
    "YXV0aG9yaXphdGlvbjogc3RyIHwgTm9uZSA9IEhlYWRlcihOb25lKSkgLT4gRmlsZVJlc3BvbnNl"
    "Og0KICAgICAgICBfY2hlY2tfYXBpX2tleShhdXRob3JpemF0aW9uLCBhcGlfa2V5KQ0KICAgICAg"
    "ICBpZiBub3QgUGF0aChwYXRoKS5leGlzdHMoKToNCiAgICAgICAgICAgIHJhaXNlIEhUVFBFeGNl"
    "cHRpb24oNDA0LCBmIkFycXVpdm8gbmFvIGVuY29udHJhZG86IHtwYXRofSIpDQogICAgICAgIHJl"
    "dHVybiBGaWxlUmVzcG9uc2UocGF0aCwgbWVkaWFfdHlwZT0iYXVkaW8vd2F2IikNCg0KICAgIEBh"
    "cHAuYXBpX3JvdXRlKCIve2Z1bGxfcGF0aDpwYXRofSIsIG1ldGhvZHM9WyJHRVQiLCAiUE9TVCJd"
    "KQ0KICAgIGFzeW5jIGRlZiBwcm94eV9wYXNzdGhyb3VnaChmdWxsX3BhdGg6IHN0ciwgcmVxdWVz"
    "dDogUmVxdWVzdCkgLT4gUmVzcG9uc2U6DQogICAgICAgIGJvZHkgPSBhd2FpdCByZXF1ZXN0LmJv"
    "ZHkoKQ0KICAgICAgICBmb3J3YXJkZWRfaGVhZGVycyA9IHsNCiAgICAgICAgICAgIGtleTogdmFs"
    "dWUgZm9yIGtleSwgdmFsdWUgaW4gcmVxdWVzdC5oZWFkZXJzLml0ZW1zKCkgaWYga2V5Lmxvd2Vy"
    "KCkgIT0gImhvc3QiDQogICAgICAgIH0NCiAgICAgICAgYXN5bmMgd2l0aCBodHRweC5Bc3luY0Ns"
    "aWVudCgpIGFzIHVwc3RyZWFtOg0KICAgICAgICAgICAgdXBzdHJlYW1fcmVzcG9uc2UgPSBhd2Fp"
    "dCB1cHN0cmVhbS5yZXF1ZXN0KA0KICAgICAgICAgICAgICAgIHJlcXVlc3QubWV0aG9kLA0KICAg"
    "ICAgICAgICAgICAgIGYie2FjZXN0ZXBfYmFzZV91cmx9L3tmdWxsX3BhdGh9IiwNCiAgICAgICAg"
    "ICAgICAgICBwYXJhbXM9cmVxdWVzdC5xdWVyeV9wYXJhbXMsDQogICAgICAgICAgICAgICAgaGVh"
    "ZGVycz1mb3J3YXJkZWRfaGVhZGVycywNCiAgICAgICAgICAgICAgICBjb250ZW50PWJvZHksDQog"
    "ICAgICAgICAgICAgICAgdGltZW91dD02MC4wLA0KICAgICAgICAgICAgKQ0KICAgICAgICByZXNw"
    "b25zZV9oZWFkZXJzID0gew0KICAgICAgICAgICAga2V5OiB2YWx1ZQ0KICAgICAgICAgICAgZm9y"
    "IGtleSwgdmFsdWUgaW4gdXBzdHJlYW1fcmVzcG9uc2UuaGVhZGVycy5pdGVtcygpDQogICAgICAg"
    "ICAgICBpZiBrZXkubG93ZXIoKSBub3QgaW4gKCJjb250ZW50LWxlbmd0aCIsICJ0cmFuc2Zlci1l"
    "bmNvZGluZyIpDQogICAgICAgIH0NCiAgICAgICAgcmV0dXJuIFJlc3BvbnNlKA0KICAgICAgICAg"
    "ICAgY29udGVudD11cHN0cmVhbV9yZXNwb25zZS5jb250ZW50LA0KICAgICAgICAgICAgc3RhdHVz"
    "X2NvZGU9dXBzdHJlYW1fcmVzcG9uc2Uuc3RhdHVzX2NvZGUsDQogICAgICAgICAgICBoZWFkZXJz"
    "PXJlc3BvbnNlX2hlYWRlcnMsDQogICAgICAgICkNCg0KICAgIHJldHVybiBhcHANCg0KDQppZiBf"
    "X25hbWVfXyA9PSAiX19tYWluX18iOg0KICAgIGltcG9ydCBvcw0KDQogICAgaW1wb3J0IHV2aWNv"
    "cm4NCg0KICAgIHV2aWNvcm4ucnVuKA0KICAgICAgICBjcmVhdGVfYXBwKG9zLmVudmlyb25bIkFD"
    "RVNURVBfSU5URVJOQUxfVVJMIl0sIG9zLmVudmlyb25bIkFDRV9TVEVQX0FQSV9LRVkiXSksDQog"
    "ICAgICAgIGhvc3Q9IjAuMC4wLjAiLA0KICAgICAgICBwb3J0PWludChvcy5lbnZpcm9uLmdldCgi"
    "UFJPWFlfUE9SVCIsICI4MTg4IikpLA0KICAgICkNCg=="
)


def write_proxy_server_script(dest_path: Path) -> Path:
    """Decode the embedded proxy_server.py source and write it to `dest_path`.

    Kaggle never uploads proxy_server.py as a sibling file (see the
    _PROXY_SERVER_SOURCE_B64 comment above), so main() calls this to
    materialize it on disk before launching it as a subprocess. Returns
    dest_path.
    """
    dest_path = Path(dest_path)
    dest_path.write_bytes(base64.b64decode(_PROXY_SERVER_SOURCE_B64))
    return dest_path


def main():
    import logging
    import os
    import shutil
    import subprocess
    import sys
    import time

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    secrets_dir = resolve_secrets_dataset_dir(Path("/kaggle/input"), _SECRETS_DATASET_REF)
    logger.info(f"Lendo secrets de: {secrets_dir}")
    secrets = load_secrets(secrets_dir)
    validate_secrets(secrets, ["NGROK_AUTHTOKEN", "NGROK_DOMAIN", "ACE_STEP_API_KEY"])
    ngrok_authtoken = secrets["NGROK_AUTHTOKEN"]
    ngrok_domain = secrets["NGROK_DOMAIN"]
    api_key = secrets["ACE_STEP_API_KEY"]

    def log_disk_usage(label: str) -> None:
        usage = shutil.disk_usage("/kaggle/working")
        logger.info(
            f"Disco em /kaggle/working ({label}): "
            f"{usage.free / 2**30:.1f}GiB livres de {usage.total / 2**30:.1f}GiB"
        )

    log_disk_usage("antes do clone")

    repo_dir = Path("/kaggle/working/ACE-Step-1.5")
    if not repo_dir.exists():
        logger.info(f"Clonando {_ACESTEP_REPO_URL} @ {_ACESTEP_REPO_COMMIT}...")
        # `git clone --depth 1` only shallow-clones a branch tip, not an
        # arbitrary SHA (not reliably supported across git versions) -- so
        # pin via init/remote/fetch-by-SHA/checkout instead, which still
        # only fetches the one pinned commit (shallow).
        subprocess.run(["git", "init", str(repo_dir)], check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", _ACESTEP_REPO_URL],
            cwd=str(repo_dir),
            check=True,
        )
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", _ACESTEP_REPO_COMMIT],
            cwd=str(repo_dir),
            check=True,
        )
        subprocess.run(
            ["git", "checkout", "-b", "main", "FETCH_HEAD"],
            cwd=str(repo_dir),
            check=True,
        )
    else:
        logger.info(f"{repo_dir} ja existe, pulando o clone.")
    log_disk_usage("depois do clone")

    # Confirmed live: the upstream acestep package sets self.dtype=float16
    # on pre-Ampere CUDA GPUs (T4/V100, compute capability < 8.0). float16
    # (5 exponent bits) can't represent this bf16-trained checkpoint's
    # activation range, and generation with non-empty lyrics deterministically
    # produces NaN/Inf latents partway through -- this is a known, currently
    # unfixed upstream bug (github.com/ace-step/ACE-Step-1.5/issues/1243,
    # closed "not planned"; the runtime's own suggested `ACESTEP_DTYPE=float32`
    # env var isn't wired to anything in this codebase, confirmed by reading
    # the source). A community fork (github.com/peter571/ACE-Step-1.5/tree/
    # fix-float32) fixes this by defaulting pre-Ampere CUDA to float32 instead
    # of float16 -- patch just that one line rather than pull in the whole
    # fork (which is 21 commits behind upstream).
    orchestrator_path = repo_dir / "acestep/core/generation/handler/init_service_orchestrator.py"
    orchestrator_src = orchestrator_path.read_text(encoding="utf-8")
    _old_dtype_block = (
        "                else:\n"
        "                    self.dtype = torch.float16\n"
        "                    logger.info(\n"
        '                        "[initialize_service] Pre-Ampere CUDA detected: "\n'
        '                        "using float16 instead of bfloat16."\n'
        "                    )\n"
    )
    _new_dtype_block = (
        "                else:\n"
        "                    self.dtype = torch.float32\n"
        "                    logger.info(\n"
        '                        "[initialize_service] Pre-Ampere CUDA detected: "\n'
        '                        "using float32 (not float16) -- avoids NaN/Inf in "\n'
        '                        "lyric conditioning, confirmed live -- see "\n'
        '                        "github.com/ace-step/ACE-Step-1.5/issues/1243."\n'
        "                    )\n"
    )
    if _new_dtype_block in orchestrator_src:
        logger.info("Patch de dtype (float32 em pre-Ampere) ja aplicado, pulando.")
    elif _old_dtype_block in orchestrator_src:
        orchestrator_path.write_text(
            orchestrator_src.replace(_old_dtype_block, _new_dtype_block), encoding="utf-8"
        )
        logger.info("Patch de dtype (float32 em pre-Ampere) aplicado.")
    else:
        raise RuntimeError(
            "O codigo de selecao de dtype pre-Ampere do acestep mudou "
            "upstream -- o patch float16->float32 nao bate mais, atualize "
            "ace_step_server.py (ver acestep/core/generation/handler/"
            "init_service_orchestrator.py)"
        )

    # Confirmed live: requirements.txt's `flash-attn` line has a prebuilt
    # wheel only for win32 -- on Kaggle's Linux kernel it falls through to
    # pip building flash-attn from source, which sat silently (no output)
    # for 20+ minutes with no sign of finishing. Flash Attention is
    # optional and auto-detected at runtime per the acestep package's own
    # GPU_COMPATIBILITY.md ("Flash Attention is auto-detected and enabled
    # when available"), so skip it entirely rather than pay for a slow,
    # fragile from-source build we don't need.
    requirements_path = repo_dir / "requirements.txt"
    all_lines = requirements_path.read_text(encoding="utf-8").splitlines()

    def _is_flash_attn(line: str) -> bool:
        # PEP 503 treats "-" and "_" as equivalent in package names, so
        # match both spellings (flash-attn / flash_attn), case-insensitive.
        normalized = line.strip().lower().replace("_", "-")
        return normalized.startswith("flash-attn")

    kept = [line for line in all_lines if not _is_flash_attn(line)]
    dropped_count = len(all_lines) - len(kept)
    if dropped_count == 0:
        raise RuntimeError(
            "Nenhuma linha 'flash-attn'/'flash_attn' encontrada em "
            f"{requirements_path} -- o requirements.txt do acestep mudou "
            "upstream (dependencia renomeada, movida para outro arquivo, ou "
            "reformatada) e o filtro deste script nao bate mais. Sem esse "
            "filtro, o pip tenta compilar flash-attn do zero, o que trava "
            "silenciosamente por 20+ minutos (o problema que este codigo "
            "existe para evitar) -- atualize ace_step_server.py."
        )
    logger.info(f"Filtrando requirements.txt: {dropped_count} linha(s) de flash-attn removida(s).")

    filtered_requirements_path = repo_dir / "requirements-no-flash-attn.txt"
    filtered_requirements_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    # --no-cache-dir: /kaggle/working ran out of disk on the first live
    # run of this kernel (confirmed live) -- torch's CUDA 12.8 wheel alone
    # is multiple GiB, and pip's default cache keeps a second copy of
    # every downloaded wheel on top of the installed package files.
    logger.info("Instalando dependencias do acestep (sem flash-attn)...")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir",
            "-r", str(filtered_requirements_path),
        ],
        cwd=str(repo_dir),
        check=True,
    )
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir", "-U",
            "pyngrok", "fastapi", "uvicorn", "httpx", "demucs",
        ],
        check=True,
    )
    log_disk_usage("depois do pip install")

    from pyngrok import ngrok

    env = os.environ.copy()
    env.update(
        {
            "ACESTEP_API_HOST": "0.0.0.0",
            "ACESTEP_API_PORT": str(_ACESTEP_PORT),
            "ACESTEP_API_KEY": api_key,
            "ACESTEP_CONFIG_PATH": _ACESTEP_MODEL_CONFIG,
            # Not "auto": confirmed live, a real generation (240s, 69%
            # through) failed with "Generation produced NaN or Inf latents"
            # in float16 -- read the acestep source
            # (acestep/core/generation/handler/init_service_loader.py) to
            # find the real cause, since the error message's suggested
            # `ACESTEP_DTYPE=float32` isn't an env var the code actually
            # reads anywhere (only appears in that hint string). The loader
            # already has a guard against exactly this failure mode --
            # pre-Ampere GPUs (T4 = Turing = compute capability 7.5) fall
            # back to "eager" attention (upcasts softmax to float32,
            # avoiding the fp16 SDPA overflow) -- but the guard's condition
            # is `device == "cuda"`, an exact string match. Passing
            # `device="auto"` through (our own default, matching the
            # package's own env-var default) never matches that check, so
            # the guard silently never fires and SDPA's fp16 overflow goes
            # unprotected. Pass "cuda" explicitly so the check matches.
            # Importante: essa mudanca sozinha NAO resolveu o NaN (confirmado
            # ao vivo -- a geracao ainda falhou com o mesmo erro depois dela);
            # o fix de verdade e o patch de dtype acima (float16 -> float32).
            # Mantemos isso mesmo assim porque "auto" tambem bloquearia outras
            # guards de pre-Ampere de dispararem corretamente.
            "ACESTEP_DEVICE": "cuda",
            "ACESTEP_DOWNLOAD_SOURCE": "huggingface",
        }
    )

    logger.info(f"Subindo acestep.api_server (config={_ACESTEP_MODEL_CONFIG})...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "acestep.api_server"],
        cwd=str(repo_dir),
        env=env,
    )

    proxy_script_path = write_proxy_server_script(Path("/kaggle/working/proxy_server.py"))
    logger.info(f"Subindo proxy_server.py (porta publica {_PROXY_PORT})...")
    proxy_env = os.environ.copy()
    proxy_env["ACESTEP_INTERNAL_URL"] = f"http://127.0.0.1:{_ACESTEP_PORT}"
    proxy_env["ACE_STEP_API_KEY"] = api_key
    proxy_env["PROXY_PORT"] = str(_PROXY_PORT)
    proxy_process = subprocess.Popen(
        [sys.executable, str(proxy_script_path)],
        env=proxy_env,
    )

    ngrok.set_auth_token(ngrok_authtoken)
    try:
        tunnel = ngrok.connect(_PROXY_PORT, "http", domain=ngrok_domain)
    except Exception:
        logger.exception(
            f"Falha ao abrir tunel ngrok no dominio {ngrok_domain} -- uma sessao "
            "anterior do Kaggle pode ainda estar segurando esse dominio; pare "
            "essa sessao antiga antes de reenviar o kernel"
        )
        server_process.terminate()
        proxy_process.terminate()
        raise
    logger.info(f"API publica em: {tunnel.public_url}")
    print(f"API publica em: {tunnel.public_url}")

    processes = {"acestep.api_server": server_process, "proxy_server": proxy_process}
    while True:
        dead_name = first_dead_process(processes)
        if dead_name is not None:
            return_code = processes[dead_name].poll()
            logger.error(f"{dead_name} encerrou sozinho (codigo {return_code})")
            # `or 1`: mesmo uma saida "limpa" (codigo 0) precisa ser reportada
            # como falha do kernel -- este kernel so existe para rodar para
            # sempre como servidor, entao qualquer saida de um dos dois
            # processos e uma falha, e um exit code 0 faria o Kaggle mostrar
            # "complete" como se tivesse dado certo.
            raise SystemExit(return_code or 1)
        time.sleep(60)


if __name__ == "__main__":
    main()
