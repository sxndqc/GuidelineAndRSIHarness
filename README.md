# Guideline and RSI Harness

Fixed-weight annotation agents with guideline retrieval, purchased examples,
persistent notes, and optional sandboxed programs.

**2026-10-06: real diagnostic experiments and a six-page paper sample are available.
The complete ACL study is not finished.** Network 403 was resolved. A subsequent
real inference request returned `429 / credit_balance_exhausted`; API calls are
paused. The user has reauthorized the official Codex CLI subscription channel;
real structured calls with GPT-6-Sol and GPT-6-Luna now succeed. A separate clean
follow-up batch is being prepared. Unequal earlier provider failures invalidate clean capability comparisons.

## Review the actual work

- [Paper PDF](paper/main.pdf) / [source](paper/main.tex)
- [Agent results and failure accounting](results/agent-analysis.json)
- [Fixed SNACS pilot settings](research/agent-pilot-registration.json)
- [Fashionpedia pilot settings](research/fashion-pilot-registration.json)
- [Current blocker and exact diagnosis](research/inference-blocker.json)
- [SNACS manual audit](research/snacs-materials-audit.md)
- [Closest ACL paper: full-text/code review](research/closest-work-fulltext-review.md)
- [Manifesto audit](research/manifesto-audit.md) / [Fashionpedia acquisition](research/bounded-material-acquisition.md)
- Final AI reviews: [validity](research/final-pilot-validity-review.md),
  [contribution](research/final-pilot-contribution-review.md),
  [benchmarks](research/final-pilot-benchmark-review.md).

## What actually ran

- **Non-LLM controls:** 60 runs, four budgets and five paired trajectories;
  all 485 retained SNACS targets in 259 official test sentences. The pinned
  upstream scorer independently matches all 60 outputs.
- **SNACS agents:** 26 configuration loops / 624 planned prediction episodes,
  two GPT-5.4 snapshots, budgets 0/4/16 and two nested example trajectories;
  the same 24 test sentences / 50 targets / 22 documents. Mini completed 275
  predictions, the larger model 206. All failures remain in denominators.
- **Full-context control:** Mini B16 completed; larger-tier cell interrupted.
- **Fashionpedia:** real official images, 16 training and 16 validation regions;
  Mini attempted all five cells. Larger-tier comparison interrupted. This is
  given-box taxonomy-conditioned classification, not the official segmentation
  benchmark or evidence of learning an audited annotation manual.
- **Important negative diagnostic:** no formal SNACS agent executed a program.
  The program-enabled arm cannot establish effects of executable self-evolution.

The full SNACS manual contains 541 numbered example groups. B0 therefore means
zero **additional** purchased sentences. No human few-shot baseline, expert
confirmed guideline gap, reliable sufficient-example count or ACL-ready claim
is made. The three reviewers are AI agents, not human conference reviewers.

## Reproduce offline checks and controls

```bash
uv --cache-dir /tmp/guideline-uv-cache sync --frozen --extra reports
.venv/bin/python -m guideline_harness.cli fetch-streusle
.venv/bin/python -m guideline_harness.cli prepare-snacs
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m guideline_harness.cli baselines --split test --output runs/reproduced-controls
.venv/bin/python scripts/verify_upstream_scorer.py
```

STREUSLE commit: `8ba61fe4f216e7967500a862554a4fff79d25f5d`.
The source annotation license is CC BY-SA 4.0; source-text rights are separately
described upstream. Public outputs contain predictions and IDs. Full episode
traces remain local under ignored `episodes/` because they include source
materials; published trace summaries retain hashes, response IDs, usage and
resource-access metadata. Raw handbooks, images and corpus texts are not pushed.

## Materials and model runs

```bash
.venv/bin/python scripts/fetch_snacs_manual.py
.venv/bin/python scripts/acquire_fashion_bounded.py
.venv/bin/python scripts/prepare_fashion_pilot.py
```

The image downloader uses official HTTP ranges and a transfer cap rather than
fetching a 3.3GB ZIP. Its prefix training selection is deliberately documented.
Official Fashionpedia attribute IDs are sparse: use inventory membership,
not the mistaken assumption that 294 labels have IDs 0 through 293.

Configure an authorized HTTPS endpoint and secure credential binding. Current
configs use `https://api.openai.com/v1`, key environment variable `openai`, and
fixed model snapshots. Never put a key in source or chat. Native Chat Completions
with these snapshots was verified with `reasoning_effort=none`; Responses did
not authenticate through this environment binding and is not used in results.

**Restore API quota before starting more API runs.** The independently authenticated
Codex subscription adapter is available as `backend: codex_cli`; it disables native
host tools and lets the evidence controller execute only authorized actions. Copy a config to a fresh output
path and a reviewed cost ledger, then run:

```bash
.venv/bin/python -m guideline_harness.cli agent configs/my-new-run.json
.venv/bin/python scripts/run_fashion_pilot.py configs/my-new-vision-run.json
```

File-locked cost reservations cover concurrent requests. Official uncached
prices provide conservative estimates; unresolved old requests retain their
reservation and are not silently treated as free. These estimates are not an
invoice. New code records safe HTTP machine codes and stops on quota exhaustion.
A frozen run's original implementation hashes remain with its results; later
transport/scorer fixes do not retroactively change its recorded execution.

Program execution requires Linux bubblewrap and `/usr/bin/python3`:

```bash
.venv/bin/python scripts/check_sandbox.py
```

It isolates the filesystem, environment and network; there is no unsandboxed
fallback. Managed environments may require supported command escalation for
nested namespaces.

## Regenerate the paper

```bash
MPLCONFIGDIR=/tmp/guideline-mpl .venv/bin/python scripts/analyze_controls.py
MPLCONFIGDIR=/tmp/guideline-mpl .venv/bin/python scripts/analyze_agents.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Before submission: restore stable inference, reproduce the closest moderation
baseline, expand held-out data and trajectories, and test an expert-verified
convention or policy change. Manifesto has complete manuals available locally,
but its annotated corpus still requires a legitimate account/export.
