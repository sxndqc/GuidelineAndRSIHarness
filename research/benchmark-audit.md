# ACL benchmark reviewer: suitability audit

Audit date: 2026-10-06. Public maintainer GitHub files below were actually retrieved over HTTPS. This is a benchmark-design review, not completed experiments. Guidelines linked by READMEs were not all downloaded or read in full. Branch URLs are discovery evidence; a study must pin commits and guideline versions.

## Recommendation

Use UMR as the motivating structural task, STREUSLE/SNACS as the clean semantic convention task, and GUM discourse relation classification as a document/discourse transfer task. Add UD EWT as a focused, inexpensive *real annotation-policy migration* experiment, rather than pretending four public corpora automatically establish broad agent generality. STREUSLE and EWT share texts and cannot count as independent corpora or serve as blind cross-task transfer without document-level exclusion.

The benchmark is a protocol over datasets, not just a list: expose a versioned guideline, a metered labeled-example pool, a writable agent memory/harness, and evaluator-isolated held-out documents. Publish learning curves, targeted constructions, compute, and human adjudication. No candidate by itself establishes that guidelines are incomplete; an expert must audit that claim for each phenomenon.

## 1. STREUSLE / SNACS: strongest first addition

Verified sources:

- https://github.com/nert-nlp/streusle/blob/master/README.md
- https://github.com/nert-nlp/streusle/blob/master/streuseval.py
- https://github.com/nert-nlp/streusle/blob/master/psseval.py
- https://github.com/nert-nlp/streusle/blob/master/LICENSE.txt

README identifies preposition/possessive supersense guidelines, *Adposition and Case Supersenses v2.6: Guidelines for English*, https://arxiv.org/abs/1704.02134 . The dataset has established train/dev/test, >55k words and >22k supersense-tagged expressions across its semantic layers. Those numbers are not SNACS-only counts. It includes syntax from UD EWT and uses the EWT reviews source text. Annotation license is CC BY-SA 4.0; README explicitly says source sentences and PTB POS are redistributed with Google/LDC permission. Do not extrapolate that permission to unrelated LDC text.

`psseval.py` scores Role, Function, and Role+Function; distinguishes supplied target identification (`goldid`, accuracy) from predicted identification (`autoid`, P/R/F1). Gold `??` cases are explicitly excluded by the scorer. `streuseval.py` supports joint MWE/supersense evaluation and discontinuous MWEs. Start with gold targets and joint Role+Function accuracy, then add end-to-end target discovery as a separate condition. This prevents target recognition failures from masquerading as convention learning.

Why suitable: scene role versus lexical function distinguishes conceptual interpretation from lexical cues, while possessives, MWEs and lexical ambiguity produce interpretable edge cases. Version history records real label and policy updates. These are *candidate* error families, not yet expert-verified guideline omissions.

Risks: source overlap with UD EWT; full repository ships all splits, statistics, syntactic gold and lexical gold. Project only authorized inputs. Pin a release: current 5.0 changes canonical format from conllulex to CoNLL-U/MISC and README contains a stale sentence calling conllulex canonical. Prefer stable JSON adapter after version pinning. Full guideline wording and license for redistributing the guideline itself remain to be checked.

## 2. GUM discourse / DISRPT: strongest independent addition

Verified sources:

- https://github.com/amir-zeldes/gum/blob/master/README.md
- https://github.com/amir-zeldes/gum/blob/master/LICENSE.md
- https://github.com/disrpt/sharedtask2023/blob/main/README.md
- https://github.com/disrpt/sharedtask2023/blob/main/data/eng.rst.gum/README.md
- https://github.com/disrpt/sharedtask2023/blob/main/utils/rel_eval.py
- https://github.com/gucorpling/DisCoDisCo/blob/master/README.md

DISRPT 2023 GUM v9 explicitly specifies 32 fine-grained original relations and 15 coarse target labels. Documentation points to https://wiki.gucorpling.org/gum/rst for definitions. DISRPT provides gold argument spans and direction for relation classification; this is not complete discourse parsing. `rel_eval.py` computes accuracy and is labeled Apache 2.0. Add macro-F1 and phenomenon accuracy without representing those additions as the official metric. DisCoDisCo is a 2021 system baseline, not the benchmark or the official scorer; its README links official task data and training commands.

Current GUM README describes 24 genres, with 16 main genres and 8 extreme out-of-domain genres in GENTLE/test2 (26 documents). These statistics belong to current GUM, not automatically DISRPT 2023/v9. Do not combine an old release's label inventory with a new release's split counts. An extension to current GUM/eRST requires an explicit compatible conversion and inventory mapping; eRST graph prediction is a different task from 15-class DISRPT classification.

License: GUM annotations are CC BY 4.0; underlying text has heterogeneous CC licenses, including noncommercial restrictions. Reddit text is supplied as underscores and requires reconstruction. Use a documented non-Reddit subset initially and disclose changed counts; do not assert the full corpus is unrestricted CC BY.

CRITICAL LEAKAGE: `.rels` penultimate `orig_label` contains fine-grained gold and is explicitly forbidden by official rules. Removing only final `label` is insufficient. Other GUM formats contain the same document's gold syntax, entities, coreference, RST and PDTB annotations. Those files must never be mounted in the annotation agent sandbox. Official DISRPT rules also forbid training with dev for official rankings and warn against cross-corpus annotation leakage.

Why suitable: distinguishes relations such as elaboration, explanation and contrast at discourse scale and has genuine genre transfer. Natural annotation ambiguity needs expert adjudication rather than assuming every mismatch is model failure. Guideline pages themselves, paired expert judgments, and current test2 conversion were not verified here.

## 3. UD EWT: best policy-change stress test

Verified sources:

- https://github.com/UniversalDependencies/UD_English-EWT/blob/master/README.md
- https://github.com/UniversalDependencies/docs/blob/pages-source/_en/dep/appos.md
- https://github.com/UniversalDependencies/tools/blob/master/eval.py

Current README identifies v2.18, 16,622 sentences, and five web genres. It documents policy changes in v2.16/v2.17 involving name titles/embellishments (`nmod:desc`), dates, numbered entities, city-state constructions, and `you guys` (`appos` to `nmod:unmarked`). These are concrete evidence for natural convention evolution, not proof that prior guidelines failed to cover them. Sample sentences from versions must be matched and reviewed: changed annotation can reflect error correction, new policy, tokenization changes, or mixed causes.

Task: fixed gold tokens -> heads/full dependency labels; separately evaluate selected policy-change constructions. Keep syntax performance distinct from learning new convention. Counterfactual conventions should be linguistically coherent and adjudicated, not only arbitrary label renaming.

CRITICAL METRIC: official `tools/eval.py` explicitly defines LAS as HEAD+DEPREL **ignoring subtypes**. A migration such as nmod to nmod:desc can be invisible to LAS. Report official LAS plus full-label LAS/targeted edge exact match, with a transparent evaluator. `eval.py` now imports the `udtools` package; pin dependencies rather than copying the wrapper alone.

Annotations/database rights are CC BY-SA 4.0; underlying text comes from multiple copyright sources. README says much of enhanced dependencies was automatic and not manually checked. Prefer basic dependencies for gold evaluation. Basic annotations are mostly single-annotated; quoted historical agreement is not a current universal human ceiling.

Current EWT includes STREUSLE gold in MISC for 3,814 reviews sentences. Strip all unauthorized MISC annotations and deduplicate across datasets by document/text, not merely split filename. Common public UD examples and test text can be in pretraining; private newly annotated cases and policy migration strengthen the design but cannot retrospectively certify absence of contamination.

## 4. MAVEN-ERE: meaningful extension, not first MVP

Verified sources:

- https://github.com/THU-KEG/MAVEN-ERE/blob/main/README.md
- https://github.com/THU-KEG/MAVEN-ERE/blob/main/LICENSE
- linked annotation standard: https://github.com/timjogorman/RicherEventDescription/blob/master/guidelines.md

README describes 4,480 documents with coreference, temporal, causal and subevent relations and says guidelines mainly follow RED. Test gold is withheld; CodaLab submission is required. Supplied test event mentions include distractors, and only gold mentions are scored. Train/valid format groups event mentions by gold coreference chains, while test has flat mentions. Passing train-format gold event clusters to the agent while predicting coreference would leak the target.

Why suitable: ambiguity of temporal overlap, causality/precondition and subevent relations provides different convention and global consistency demands. Why defer: live evaluator availability not tested, RED-to-MAVEN adaptations not yet fully audited, numerous correlated edges make raw relation counts misleading for sample efficiency, and event candidate handling confounds relation convention learning. Repository LICENSE is GPL-3.0 text; it does not by itself establish the external dataset's separate redistribution rights. Verify data package terms before release. A local held-out split is feasible but must not be presented as the official hidden test.

## Deprioritized candidates

AMR adds a second semantic graph but is closely related to UMR, risks weak task diversity, and commonly used full corpora have LDC access restrictions; not verified in this audit. Use if graph-specific transfer becomes the central question, not just to increase the benchmark count.

ACE05 / RAMS / WikiEvents are reasonable event extraction alternatives, but do not yet pass this audit's complete guideline+license+scorer verification. The verified https://github.com/raspberryice/gen-arg/blob/master/README.md points to RAMS via JHU, ACE05 via LDC, and WikiEvents via S3; it identifies a scorer and sample predictions, but that is insufficient to assert a complete publicly redistributable annotation manual. No need to acquire all of them before a focused first study.

## Reviewer conditions for ACL claims

1. Do not claim humans require only a few examples without measuring matched human conditions, prior expertise and inter-annotator disagreement.
2. Do not claim parsers cannot use guidelines; instruction-following, retrieval, task-description transfer and supervised parsers provide relevant baselines.
3. Report annotation budget as sentences/documents, labeled decisions, unique revealed gold items, expert minutes, and examples embedded in guideline documents. Retrieving a previously labeled example spends labeled-data budget even if no new human labels it during the run.
4. Separate resource access, adaptive example selection, persistent memory, code changes, and extra inference compute. A gain over plain few-shot prompting does not identify self-evolution.
5. Freeze learned memory/harness before hidden evaluation; unseen test gold and evaluator must be inaccessible outside a trusted scoring process. Unlimited repeated dev score queries are an additional feedback budget.
6. Use document clusters for uncertainty; same-document edges and multiple annotations of the same sentence are not independent samples.
7. Estimate the example budget needed for a prespecified quality target with confidence intervals and failure-to-reach reporting, rather than claiming a universal magic number.
