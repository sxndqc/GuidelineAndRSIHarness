# Guideline and RSI Harness

Research on how fixed-weight agents adapt annotation policies through examples,
natural-language memory and executable programs.

**Status (2026-10-06): a real-data control experiment is complete; the requested
full agent study is NOT complete.** Do not interpret the non-LLM results as
agent learning, compare unrun models, or treat a data audit as a guideline-gap finding.

## Read first

- [ACL-format working paper](paper/main.pdf) / [LaTeX source](paper/main.tex)
- [Research design (Chinese)](research/research-proposal.zh.md)
- [Manifesto audit](research/manifesto-audit.md)
- [Fashionpedia audit](research/fashionpedia-audit.md)
- [Cross-domain protocol review](research/cross-domain-protocol-review.md)
- [Actual control results](results/control-table.md), [raw report](results/snacs-controls-v2/baseline-results.json)
- [Experiment status and unresolved requirements](research/experiment-status.json)

## What has actually run

Pinned official STREUSLE data; document-disjoint official splits; given-target
SNACS projection stripping other gold layers; 60 real non-LLM control runs
(3 methods × 4 labeled-sentence budgets × 5 paired trajectories) over all
485 retained targets in 259 official test sentences. Artifacts include predictions,
source hashes, purchased-example IDs, summary statistics and paired descriptive
bootstrap intervals. All 60 runs match the pinned official scorer on role,
function, joint accuracy and target denominators. Dataset text is not redistributed in this repository.

Ten regression/unit checks and a real bubblewrap isolation check are provided.
The model stub in unit tests is only a software fixture; it never produces
reported research results. The controller exposes bounded tools, meters gold,
freezes test assets and executes agent-written Python in a network-isolated
filesystem. Program execution fails closed if bubblewrap is unavailable.

**Currently implemented model track: SNACS given-target classification.**
Manifesto/Fashionpedia are audited candidate tracks, not secretly substituted
by synthetic data or a two-image API sample. No vision adapter is claimed ready.

## Reproduce the completed controls

Python 3.11+ (tested with 3.12.14), NumPy 2.3.5, scikit-learn 1.8.0.
For figures use matplotlib 3.10.8. Use the existing isolated checkout;
do not create a worktree unless specifically requested.

```bash
uv --cache-dir /tmp/guideline-uv-cache sync --frozen --extra reports
.venv/bin/python -m guideline_harness.cli fetch-streusle
.venv/bin/python -m guideline_harness.cli prepare-snacs
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m guideline_harness.cli baselines \
  --split test --output runs/reproduced-controls
```

The downloader pins commit `8ba61fe4f216e7967500a862554a4fff79d25f5d`, preserves TLS
verification, and records SHA-256 for every source. Preparation checks hashes.
One purchased example means one sentence and reveals all retained SNACS decisions
in that sentence. Gold target spans are supplied to every condition.
The source annotation license is CC BY-SA 4.0, with source-text permissions
described in the upstream README; these permissions do not cover other corpora.

The analysis script currently regenerates publication artifacts from the two
committed control-run reports and local prepared gold:

```bash
.venv/bin/python scripts/analyze_controls.py
.venv/bin/python scripts/verify_upstream_scorer.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Model experiments: explicit prerequisites

`configs/snacs-pilot.example.json` is a configuration example, not a completed run.
`configs/snacs-materials.json` deliberately remains `pending_audit`: a label
inventory is not the full guideline. Supply version-aligned, legally available
materials with hashes and an embedded-example audit before changing this status.
An `audited` string is a controller gate, not proof of expert scientific review.

The implemented provider uses an HTTPS OpenAI-compatible **Chat Completions**
endpoint. Set `ANNOTATION_API_BASE` (ending in `/v1` where required) and a secure
`ANNOTATION_API_KEY` binding; specify the exact model version in the config.
Never place credentials in source, CLI arguments, tracked files or chat.
The API's `max_completion_tokens` parameter must be supported by the selected
provider. No provider SDK or authentication-file scraping is used.

```bash
.venv/bin/python -m guideline_harness.cli agent configs/my-audited-run.json
```

Failed/truncated calls retain known metadata; unknown usage is not counted as
zero. The caller must budget actual provider cost; no price is invented.
For `notes_program`, Linux bubblewrap and `/usr/bin/python3` are required:

```bash
.venv/bin/python scripts/check_sandbox.py
```

The real test checks that host gold, repository, inherited environment marker
and external network are inaccessible. Within this managed environment it
requires the supported command-approval flow to create nested namespaces;
there is no unsandboxed fallback.

## Remaining research requirements

The existing Codex login was verified, but its minimal inference call was
blocked by the network proxy (403). The CLI login has **not** been validated as
an experimental backend, and it is not silently used as this API provider.
No model API binding or GPU was found. Network additions are saved as a draft;
saving a draft does not apply/publish it.

Manifesto Corpus needs an official key or legitimate export, full handbook,
version/split/terms checks. Fashionpedia needs official full annotations and
actual images, plus definition/attribute-completeness audits. Its two-image
API sample has a different schema and is not used for research results.

Three AI reviewer agents critiqued the design, datasets and implementation.
They are not independent human annotators or actual ACL reviewers. Their audits
are retained under `research/`. The working paper's limitations and unrun
conditions are explicit; no acceptance or novelty claim is made.
