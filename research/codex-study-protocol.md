# Codex subscription study: protocol v1 (frozen before new test inference, 2026-10-06)

This batch is separate from the interrupted GPT-5.4 API diagnostics. Official Codex CLI subscription inference uses `gpt-6-sol` and `gpt-6-luna`, both medium reasoning. These are mutable model aliases and CLI-system comparisons, not a controlled parameter-count experiment. Preserve catalog/version, source hashes, calls, usage and wall time. No API price is imputed to subscription usage.

## Estimand and tasks

Estimate the effect of persistent evidence-derived rule addenda over retrieval of the same purchased examples, conditional on pretrained models and original handbooks that already contain examples. This is not learning annotation from scratch or weight self-modification. SNACS predicts supplied-span role/function pairs. CAP PA predicts published policy codes from summaries; it does not reproduce full-document annotation. Schema-support and ambiguous-summary strata distinguish information limitations from adaptation failures.

CAP split uses label-blind normalized text plus approximate near-duplicate candidate retrieval, verified 5-word shingle Jaccard >=.85 and connected components. All family members stay in one split. Approximate LSH may miss near duplicates. Unsupported handbook codes (17 rows) are quarantined by inventory, not performance. No majority relabeling. Historical guideline-version alignment and summary sufficiency remain limitations.

## Conditions

- frozen: current purchased examples and searchable original guideline, no persistent asset changes.
- notes: same evidence; a bounded adaptation episode writes persistent notes. Evaluation can read original evidence and notes.
- moderation: one three-stage proposal per budget: dominant adaptation error pattern plus correct contrasts; IF/THEN principle with negative constraints; policy addendum. Probe before/after on purchased adaptation inputs without exemplar access; accept only strictly improved adaptation accuracy, otherwise roll back. This is an adapted addendum comparator inspired by Kim et al. (ACL 2026), not full-handbook rewriting or numerical replication. Training-set acceptance can overfit and is not heldout evidence. Probes receive the full original guideline and current assets inline, directly matching the full-guideline context convention of the comparator; update phases use material tools. This gives the comparator different context/compute allocation, which is measured, not claimed matched.

Code permission is absent from the new main comparison because two earlier development batches did not actually execute a program. Their unused optional permission cannot estimate a program effect. Therefore the new batch tests persistent policy adaptation, not unconstrained agent self-evolution.

## Sampling and evaluation

Frozen grid: nested budgets 0/4/16/64 and seeds 11/23/47, with one purchased row per training family. The same trajectory is shared across conditions/models. B0 is one common frozen starting point, not three independent adaptation runs. Exact configurations: configs/codex-study-{snacs,cap_pa}-{sol,luna}.json. SNACS: 64 documents, 114 sentences, 202 targets excluding all earlier agent-test documents. CAP: 128 families, 215 rows. Both use 16 fixed batches; 4 SNACS documents or 8 CAP families per batch. Group selection seed 20261008. Purchased budgets count one row from each distinct training family. This is a bounded study with limited interval precision, not a power-certified design.

Evaluation batches use identical groups, order and public inputs in every condition. Each batch starts from immutable assets and no previous test predictions; multiple unlabeled inputs within a batch can inform each other. This is batch-level inference, not per-instance isolation. Confidence calculations must respect the batch as the outer dependence unit, with corpus family counts reported. Outcomes retain all failures and separately report completion/validity. Failed probes cannot justify accepting a moderation update.

Primary SNACS outcome: target joint accuracy. Primary CAP outcome: row accuracy, with family-macro accuracy and observed-label/full-inventory macro-F1. Report label support (seen/unseen among purchased labels), completion and actual exposure/tool use. Use paired intervals for condition differences; three adaptation seeds are limited replication. Report per-seed trajectories without monotonic smoothing. No example-sufficiency claim if the selected quality target is not reached with uncertainty accounted for. No extrapolated asymptote from four budgets.

## Controls and safeguards

All test gold stays in the controller. Only projected inputs enter prompts; purchase ledger meters every revealed training annotation. CLI native host features are disabled and event streams audited fail-closed; this is not a claim that read-only OS sandboxing hides all host files. The program subprocess used in older runs has its separate bwrap isolation test. A negative synthetic-sentinel probe is logged. Source hashes and raw transport logs preserve protocol evidence; raw corpora/traces containing source text are not republished by default.

A static full-context control and the original small NCBI moderation workflow remain desirable calibration controls. Absence of those or inadequate test precision must be described as limitations, not disguised as completed ACL submission validation.

Quality attainment thresholds are 70%, 80%, and 90% primary accuracy, reported only for observed budgets and with uncertainty; no universal sufficient-example count. The shared run ceiling is 6,000 subscription calls. No retries selected on answer correctness. Backend/transport/isolation failure stops the affected run with partial results retained.
