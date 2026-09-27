# ACE-Step batch kernel (replaces server + ngrok tunnel)

## Motivation

The current `ace_step/` pipeline runs the ACE-Step generation model as a
long-lived Kaggle kernel exposing a REST API through a fixed-domain ngrok
tunnel (`ace_step/kernel/ace_step_server.py` + `proxy_server.py`). A live
end-to-end test (2026-09-26, generating a real 4-minute song) succeeded at
generation but stem separation failed twice with `ERR_NGROK_725`: the
ngrok account's monthly bandwidth cap was exhausted by downloading the
generated audio, which then took the whole kernel down with it (the ngrok
tunnel failing killed the process).

This spec replaces the server+tunnel model with a **batch kernel**: one
Kaggle kernel run does generation and separation for a single song
end-to-end, and the local side retrieves the result through the Kaggle
API's own kernel-output mechanism (`kernels_output`) instead of any public
HTTP endpoint. No tunnel, no bandwidth cap, no public API key.

## Current architecture (being replaced)

- `ace_step_server.py`: clones/patches `acestep`, launches
  `acestep.api_server` + `proxy_server.py`, opens a public ngrok tunnel on
  a fixed domain, and runs forever until the Kaggle session ends.
- `proxy_server.py`: FastAPI app proxying `acestep`'s endpoints and adding
  its own task-queue endpoints (`/separate_task`, `/query_separation_result`,
  `/v1/stems`) for Demucs separation, guarded by a bearer API key.
- `ace_step/client.py`: local HTTP client (`generate_music`,
  `separate_stems`, `download_audio`, `check_health`) talking to the
  public ngrok URL.
- `ace_step/orchestrator.py`: `run_generation()` (health check, lyrics,
  generate, download, master, then calls `run_separation()`) and
  `run_separation()` (submit+poll+download stems), both HTTP-driven.

## New architecture

One kernel run per song:

1. The local side generates lyrics (unchanged, `ace_step/lyrics.py`), then
   **renders a self-contained kernel script** with the job's parameters
   embedded, and pushes it to the existing kernel slug
   (`celsosoarescesar/ace-step-api`).
2. Inside the kernel: clone/patch `acestep` (unchanged setup logic), launch
   `acestep.api_server` bound to `127.0.0.1` only (no tunnel, no public
   exposure), call its `/release_task` + `/query_result` endpoints against
   `localhost` to generate the song, then run Demucs (`htdemucs_6s`) as a
   subprocess against the resulting file — all sequentially, in-process,
   no task queue needed since there is no external caller to poll it.
   Results are written to `/kaggle/working/output/` and the kernel exits
   (0 on a successful generation, non-zero if generation itself failed;
   a separation failure is recorded in `result.json` but does not fail
   the kernel run — same semantics as today).
3. The local side polls `kernels_status` until the run reaches a terminal
   state, then calls `kernels_output` to download `/kaggle/working/output/`
   (result.json + raw audio + stems), applies loudness normalization
   locally (unchanged, `ace_step/mastering.py`), and updates `songs.db`.

This removes: `proxy_server.py`, `ace_step/client.py`, the ngrok tunnel,
the `NGROK_AUTHTOKEN`/`NGROK_DOMAIN` secrets requirement, and the proxy's
own bearer-auth layer. `ACE_STEP_API_KEY` is kept (used internally by
`acestep.api_server` itself against `127.0.0.1`, no longer for anything
public), and `ACE_STEP_API_URL` in `.env` is no longer used by this
pipeline and will be removed from `.env` and from
`scripts/criar_musica.py`'s required-env check.

## Job parameter encoding

Kaggle's `script`-type kernel push only uploads the single `code_file`
(confirmed live already, see the comment above `_PROXY_SERVER_SOURCE_B64`
in `ace_step_server.py`) — there is no per-run argument passing. Rather
than provision a new Kaggle Dataset per song (extra API calls, and
dataset-to-kernel propagation has no track record of being fast/reliable
in this project), the job parameters are serialized to JSON, base64-encoded,
and embedded as a plain string constant in the rendered kernel source —
the same technique already used to embed `proxy_server.py`'s bytes. Base64
sidesteps any quoting/escaping concerns from arbitrary prompt/lyrics text
(unicode, quotes, newlines).

Job dict: `{"prompt", "lyrics", "duration", "seed", "bpm", "keyscale",
"vocal_language"}` — the same fields `generate_music()` takes today.

Rendering happens locally, once per song, into a temp kernel folder
(temp dir, not committed) containing a copy of `kernel-metadata.json` and
the rendered `.py` file, then `push_kernel()` (unchanged function) is
called against that temp folder.

## Kernel-side changes (`ace_step/kernel/ace_step_server.py`)

Kept as-is: `resolve_secrets_dataset_dir`, `load_secrets`,
`validate_secrets` (now only requires `["ACE_STEP_API_KEY"]`), the
`acestep` clone/patch logic (dtype patch, flash-attn filtering, disk
logging), and launching `acestep.api_server` as a subprocess.

Removed: `proxy_server.py` embedding/launch, `pyngrok`
install+`ngrok.connect`, the `first_dead_process` forever-loop (a batch
kernel is expected to exit).

Added, all after `acestep.api_server` reports healthy on
`127.0.0.1:{_ACESTEP_PORT}`:

- A small embedded HTTP client (a trimmed, localhost-only copy of today's
  `generate_music`'s `_post`/poll-loop logic — no bearer auth needed
  against localhost) that submits `/release_task` with the embedded job
  and polls `/query_result` until done or its own timeout.
- On success: copy the resulting file (path resolved the same way
  `parse_audio_path` does today) to `/kaggle/working/output/raw.wav`.
- Then, in a `try/except` that never lets a separation failure fail the
  run: run Demucs (`htdemucs_6s`) as a subprocess against `raw.wav`,
  writing to `/kaggle/working/output/stems/{vocals,drums,bass,guitar,
  piano,other}.wav`.
- Write `/kaggle/working/output/result.json`:
  `{"generation_status": "done"|"error", "generation_error": str|null,
  "stems_status": "done"|"error", "stems_error": str|null}`.
- Delete `/kaggle/working/ACE-Step-1.5` (the cloned repo, which lives
  under `/kaggle/working` and would otherwise be pulled down as part of
  the kernel's output) before exiting, so `kernels_output` only pulls
  `/kaggle/working/output/`. HuggingFace model weights are cached outside
  `/kaggle/working` (confirmed by existing `ACESTEP_DOWNLOAD_SOURCE`
  config) and are not part of kernel output regardless.
- `sys.exit(0)` if `generation_status == "done"`, else `sys.exit(1)` —
  mirrors today's "generation failure fails the kernel, separation
  failure doesn't" semantics, just moved from Python-exception-propagation
  into the exit code + `result.json`.

## Local-side changes (`ace_step/orchestrator.py`)

`run_generation()` and `run_separation()` collapse into a single
`run_generation()` (no more two-phase HTTP calls, so there is no
ephemeral-remote-file problem to work around anymore — that whole
class of bug goes away):

1. Generate lyrics (unchanged).
2. Render the kernel folder (new `ace_step/kernel_render.py` module:
   `render_job_kernel(job: dict, dest_dir: Path) -> Path`) and
   `kernels.push_kernel(dest_dir)`.
3. Poll `kernels.get_kernel_status(ref)` until status is one of
   `{"complete", "error", "cancel_acknowledged"}` (terminal) or `timeout`
   seconds elapse (default 2700s / 45 min — a batch run pays the full
   environment-setup cost every time, observed live at ~6-7 minutes,
   plus generation and separation time; no warm-session amortization
   anymore, which is the accepted tradeoff for dropping ngrok). Poll
   interval: 20s.
4. `kernels.pull_kernel_output(ref, tmp_dir)`.
5. Read `tmp_dir/output/result.json`. If missing (kernel crashed before
   writing it, e.g. during setup) or `generation_status != "done"`,
   record `status="error"` with `get_kernel_status`'s `failure_message`
   and/or `result.json`'s `generation_error` — whichever is available —
   same "never raises, always records on the row" contract as today.
6. On success: move `tmp_dir/output/raw.wav` into place, run
   `mastering.normalize_loudness` (unchanged) into `{song_id}_master.wav`,
   record `status="done"`.
7. Regardless of step 6, read `stems_status`/`stems_error` from
   `result.json`: if `"done"`, move each `tmp_dir/output/stems/*.wav` into
   `{song_id}_stem_{name}.wav` and record `stems_status="done"` with the
   `stem_*_path` fields (same schema as today); if `"error"`, record
   `stems_status="error"` with `stems_error_message`.
8. Clean up `tmp_dir` and the temp kernel folder from step 2.

`songs.db` schema is unchanged (no migration needed) — `remote_file_ref`
becomes unused (nothing else in the codebase reads it) and is dropped
from `song_db.create_song`/`update_song`'s call sites, but the column
itself is left in place rather than a migration, consistent with how this
project has treated other now-unused columns.

## Removed files

- `ace_step/kernel/proxy_server.py`
- `ace_step/client.py`
- `tests/test_ace_step_client.py`
- The `_PROXY_SERVER_SOURCE_B64` embedding and
  `test_write_proxy_server_script_matches_repo_file` in
  `tests/test_ace_step_kernel_server.py`

## CLI / `.env` impact

- `scripts/criar_musica.py`: drops the `ACE_STEP_API_URL`/`ACE_STEP_API_KEY`
  env check in favor of just needing Kaggle credentials (already required
  by `kaggle_client.py` for `push_kernel`/`get_kernel_status`); `--timeout`
  default changes from `300.0` to `2700.0` with updated help text
  describing it as the kernel-run budget, not an HTTP poll budget.
- `.env`: remove both `ACE_STEP_API_URL` and `ACE_STEP_API_KEY`. Confirmed
  by grep: locally, `ACE_STEP_API_KEY` is only ever read by `client.py`
  (deleted) and `criar_musica.py`'s env check (dropped above). The kernel's
  own copy of `ACE_STEP_API_KEY` comes from the Kaggle secrets dataset
  (`secrets.json`, via `load_secrets`), independent of local `.env` — that
  copy is unaffected by this change.

## Error handling

- Kernel push fails (`KaggleResourceError` from `push_kernel`): recorded
  as `status="error"` immediately, no polling attempted.
- Polling exceeds `timeout`: recorded as `status="error"` with a message
  noting the kernel may still be running remotely and its ref, so it can
  be inspected manually later (matches today's timeout-message style in
  `ace_step_client.generate_music`).
- Kernel reaches `"error"` or `"cancel_acknowledged"`: recorded as
  `status="error"` using `get_kernel_status`'s `failure_message`.
- `kernels_output` succeeds but `result.json` is missing or unparseable:
  recorded as `status="error"` with a message saying the kernel likely
  crashed before writing output, plus whatever `failure_message` Kaggle
  reported.
- Any of the above: `run_generation` still never raises — same contract
  as today.

## Testing

- `tests/test_ace_step_orchestrator.py` is rewritten against the new
  `run_generation()` (push/poll/pull, mocked via fakes for
  `kernels.push_kernel`/`get_kernel_status`/`pull_kernel_output`) instead
  of today's HTTP-client mocks — same "never raises" contract, same
  status/stems_status/error-message assertions, just driven by kernel
  states instead of HTTP responses.
- `render_job_kernel`: given a job dict, produces a kernel folder whose
  `.py` file, when imported (no GPU/Kaggle needed, following the existing
  "importable without heavy deps" convention), decodes back to the exact
  same job dict — round-trip test, plus a case with unicode/quotes/
  newlines in `lyrics` to exercise the base64 escaping story.
- `result.json` parsing: valid done/done, done/error, and missing-file
  cases, verifying `run_generation`'s recorded `status`/`stems_status`/
  error messages for each.
- Kernel status → terminal/non-terminal mapping: table-driven test over
  `{"queued", "running", "complete", "error", "cancel_acknowledged"}` plus
  an unrecognized value (must not be treated as terminal — keep polling
  rather than silently misclassifying an unknown status as done).
- `tests/test_ace_step_kernel_server.py`'s existing coverage of the
  clone/patch/disk-logging helpers is kept as-is (untouched by this
  change); only the proxy-embedding test and anything asserting the
  forever-loop/ngrok behavior is removed or updated to match the new
  exit-on-completion behavior.
- No test attempts to actually run Demucs or `acestep` — those stay
  verified live only, consistent with
  `[[feedback_verify_third_party_apis_live]]`.

## Open risks (to confirm live during implementation)

- Whether `kernels_output` behaves sensibly against a kernel that exited
  non-zero (partial output, if any, should still be retrievable for
  debugging) — not verified in this codebase yet.
- Actual end-to-end wall-clock time per song under the new model (the
  2700s default is an estimate from the one live run so far, which did
  not include stem separation time); may need adjusting after the first
  live batch run.
- Whether `kernels_output` preserves the `/kaggle/working/output/`
  subdirectory as-is (`orchestrator.py`'s `tmp_pulled_dir / "output" / ...`
  paths assume it does) — flagged by final review as the most likely first
  bug in Task 9; if it doesn't, locate `result.json` via a fallback
  `rglob("result.json")` instead of hardcoding the `output/` prefix.
- Where the acestep checkpoints actually land: the kernel's own comment
  (`ace_step_server.py`, near `_ACESTEP_MODEL_CONFIG`) records that a
  checkpoint download once filled `/kaggle/working`'s disk, which would
  put ~10GB of model weights inside the same tree `kernels_output` pulls
  from. Confirm in Task 9 whether that happened again; if so, point the
  acestep checkpoint/HF cache dir outside `/kaggle/working` (e.g. `/tmp`)
  so a crashed-kernel error-path pull (`orchestrator.py`'s best-effort pull
  after a non-`complete` kernel status) can't drag down the weights.
- The kernel-status race flagged by final review: the kernel slug is
  reused for every run and Kaggle's status API takes no per-push version,
  so in principle a `complete` status on the very first poll right after
  push could be a stale read of the *previous* run. `orchestrator.py`'s
  `_wait_for_kernel_terminal` now refuses to trust a `complete` status
  until a non-terminal one has been observed first (mitigates the risk
  without changing the job/`result.json` wire shapes) — this heuristic
  itself is unverified against real Kaggle timing; watch for it
  unexpectedly stalling in Task 9 if Kaggle ever reports `complete`
  without a `queued`/`running` status in between for a genuinely fresh
  run.
