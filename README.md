# Guideline and RSI Harness

Fixed-weight annotation agents with guideline retrieval, purchased examples,
persistent notes, and optional sandboxed programs.

**2026-10-07: the 112-cell subscription experiment matrix is complete.**
All four task/model runs finished by 03:24 UTC. The study compares GPT-6-Sol and
GPT-6-Luna on SNACS and CAP Pennsylvania, three methods, budgets 0/4/16/64,
and three paired example trajectories. Of 1,792 evaluation batches, 1,728
completed, 55 exhausted the action cap, and 9 were refused; every target remains
in the denominator. The ledger records 15,896 requests, including interruptions.
Forty-five matched non-LLM control cells also completed.

At B64, notes-minus-retrieval descriptive intervals contain zero for all four
task/model combinations. This does not establish a general benefit of persistent
notes or a sufficient example count. The seven-page paper is a review sample,
not an ACL-ready claim. UMR has **not** been experimentally evaluated.

## Review the actual work

- [Current cross-domain paper PDF](paper/subscription-study.pdf) / [source](paper/subscription-study.tex)
- [Live execution status](research/subscription-supervisor-status.json) / [new study analysis](results/subscription-study-analysis.json)
- [Frozen design](research/codex-study-protocol.md) / [operational continuation amendment](research/subscription-resumption-amendment.md)
- [Earlier API diagnostic paper](paper/main.pdf) / [source](paper/main.tex)
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

The new subscription batch has a fixed test sample of 64 SNACS documents
(114 sentences, 202 targets) and 128 CAP families (215 records). It compares
frozen example retrieval, persistent notes, and an error-guided addendum
comparator. Forty-five matched non-LLM control cells are complete. All 112 model configuration cells completed; individual prediction failures remain explicitly counted.
CAP preparation groups exact and approximate near duplicates before splitting,
keeps conflicting labels, and quarantines 17 unsupported-code rows. Its handbook
and historical label alignment, summary sufficiency, and sparse test-class
coverage remain explicit limitations.

The separate earlier diagnostics are:

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
.venv/bin/python scripts/fetch_cap_pa.py
.venv/bin/python scripts/group_cap_near_duplicates.py
.venv/bin/python scripts/prepare_cap_pa.py
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

## Subscription study and long-run recovery

Use official `codex login --device-auth` when needed; never extract tokens into
an API-key adapter. The current session has already logged in successfully.
Runs use `configs/codex-study-*.json`. Original settings and implementation hashes
remain with each run. Explicit resume changes only resource/scheduling settings;
completed predictions, refusals and tool exhaustion are never rerun for selection.
Legacy first-capture content hashes and posthoc interruption classifications are
marked in provenance rather than described as contemporaneous evidence.

```bash
.venv/bin/python scripts/analyze_subscription_study.py
MPLCONFIGDIR=/tmp/guideline-mpl XDG_CACHE_HOME=/tmp/guideline-cache .venv/bin/python scripts/render_subscription_paper.py
```

The `scripts/supervise_subscription_study.py` process checked progress,
regenerated the PDF every five minutes, and committed/pushed final outcomes
when all jobs completed or stopped with a recorded blocker. It is now stopped. It has a process lock,
a finite deadline, and bounded continuation attempts. It cannot make provider
capacity or quota available. Check its status before launching another copy.
The completed API diagnostic paper is preserved separately from the live paper.
