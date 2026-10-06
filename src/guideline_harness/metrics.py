from __future__ import annotations
import numpy as np
from sklearn.metrics import f1_score
from .ontology import SNACS_LABELS

INVALID = "__INVALID__"

def score_snacs(records, predictions):
    roles, functions, proles, pfunctions, joint, groups = [], [], [], [], [], []
    exact_sentences = valid_sentences = 0
    for row in records:
        pred = predictions.get(row["id"], {})
        if not isinstance(pred, dict):
            pred = {}
        valid = set(pred) == set(row["gold"])
        sentence_correct = True
        for target, pair in row["gold"].items():
            candidate = pred.get(target)
            wellformed = isinstance(candidate, list) and len(candidate) == 2 and all(isinstance(x,str) for x in candidate)
            guess = candidate if wellformed else [INVALID, INVALID]
            valid = valid and wellformed and all(x in SNACS_LABELS for x in guess)
            roles.append(pair[0]);functions.append(pair[1]);proles.append(guess[0]);pfunctions.append(guess[1])
            ok = guess == pair
            joint.append(ok);groups.append(row["group"])
            sentence_correct = sentence_correct and ok
        # Extra targets are invalid and defeat sentence exact match, but cannot erase target errors.
        exact_sentences += bool(sentence_correct and valid)
        valid_sentences += bool(valid)
    if not joint:
        raise ValueError("No evaluated SNACS targets")
    return {"sentences": len(records), "targets": len(joint), "documents": len(set(groups)),
            "role_accuracy": float(np.mean(np.array(roles)==np.array(proles))),
            "function_accuracy": float(np.mean(np.array(functions)==np.array(pfunctions))),
            "joint_accuracy": float(np.mean(joint)),
            "role_macro_f1": float(f1_score(roles, proles, labels=sorted(set(roles)), average='macro',zero_division=0)),
            "function_macro_f1": float(f1_score(functions, pfunctions, labels=sorted(set(functions)), average='macro',zero_division=0)),
            "sentence_exact": exact_sentences/len(records), "valid_output_rate": valid_sentences/len(records)}

def cluster_interval(records, predictions, seed=42, repeats=2000):
    """CI over held-out document sampling, NOT over adaptation randomness."""
    totals = {}
    for row in records:
        p = predictions.get(row["id"], {})
        if not isinstance(p,dict): p = {}
        good, n = totals.get(row["group"], (0,0))
        totals[row["group"]] = (good+sum(p.get(k)==v for k,v in row["gold"].items()), n+len(row["gold"]))
    a = np.array(list(totals.values()), dtype=float)
    rng = np.random.default_rng(seed)
    samples = a[rng.integers(len(a),size=(repeats,len(a)))].sum(axis=1)
    low, high = np.quantile(samples[:,0]/samples[:,1],[.025,.975])
    return {"low": float(low), "high": float(high), "unit": "document", "repeats": repeats,
            "scope": "test-document uncertainty conditional on this adaptation run"}
