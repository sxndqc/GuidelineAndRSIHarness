"""Real-data non-LLM controls. These are NOT agent/self-evolution results."""
from __future__ import annotations
from collections import Counter, defaultdict
import json
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .data import read_json, write_json, digest
from .protocol import BudgetLedger, trajectory
from .metrics import score_snacs, cluster_interval

def examples(rows):
    for row in rows:
        for target in row["input"]["targets"]:
            yield row, target, row["gold"][target["id"]]

def target_text(row, target):
    marked = set(target["token_indices"])
    tokens = [f"TARGET_{w}" if i+1 in marked else w for i,w in enumerate(row["input"]["tokens"])]
    return target["text"].lower() + " TARGET " + " ".join(tokens).lower()

def predict(method, purchased, evaluation):
    training = list(examples(purchased))
    result = {r["id"]:{} for r in evaluation}
    if not training:
        return result
    majority = Counter(tuple(p) for _,_,p in training).most_common(1)[0][0]
    by_word = defaultdict(Counter)
    for _,target,pair in training:
        by_word[target["text"].lower()][tuple(pair)] += 1
    query = [(row, target) for row in evaluation for target in row["input"]["targets"]]
    # The predictor never accesses evaluation gold, even incidentally.
    if method == "tfidf_nearest":
        vec = TfidfVectorizer(ngram_range=(1,2), min_df=1, token_pattern=r"(?u)\b\w+\b")
        mat = vec.fit_transform([target_text(r,t) for r,t,_ in training])
        sims = vec.transform([target_text(r,t) for r,t in query]) @ mat.T
        nearest = np.asarray(sims.argmax(axis=1)).ravel()
        maxvals = np.asarray(sims.max(axis=1).toarray()).ravel()
    for i,(row,target) in enumerate(query):
        if method == "majority": pair = majority
        elif method == "lexical_majority":
            counts = by_word.get(target["text"].lower())
            pair = counts.most_common(1)[0][0] if counts else majority
        elif method == "tfidf_nearest":
            pair = training[int(nearest[i])][2] if maxvals[i]>0 else majority
        else: raise ValueError(method)
        result[row["id"]][target["id"]] = list(pair)
    return result

def run_baselines(data_root, output_root, budgets=(4,16,64,128), seeds=(11,23,47,83,101), split="test"):
    if split not in {"dev","test"}: raise ValueError("Evaluation split must be dev or test")
    data_root, output_root = Path(data_root), Path(output_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError('Use a fresh output directory; baseline runs cannot overwrite previous results')
    train = read_json(data_root/"private/train.json")
    evaluation = read_json(data_root/f"private/{split}.json")
    rows = []
    for seed in seeds:
        order = trajectory(train,seed)
        for budget in budgets:
            if budget > len(order) or budget < 1: raise ValueError("Invalid supervised baseline budget")
            ledger = BudgetLedger(budget)
            purchased = [ledger.reveal(r) for r in order[:budget]]
            for method in ("majority","lexical_majority","tfidf_nearest"):
                public_evaluation = [{k:v for k,v in r.items() if k != 'gold'} for r in evaluation]
                pred = predict(method,purchased,public_evaluation)
                record = {"method":method,"model_type":"non-LLM control","budget":budget,"seed":seed,"split":split,
                          "supervision":ledger.summary(),"purchased_ids":[r['id'] for r in purchased],
                          "predictions_sha256":digest(pred),"metrics":score_snacs(evaluation,pred)}
                rows.append(record)
                write_json(output_root/"predictions"/f"{method}-b{budget}-s{seed}.json",pred)
    summary=[]
    for budget in budgets:
        for method in ("majority","lexical_majority","tfidf_nearest"):
            selected=[r for r in rows if r['budget']==budget and r['method']==method]
            vals=np.array([r['metrics']['joint_accuracy'] for r in selected])
            summary.append({"method":method,"budget":budget,"runs":len(vals),
                            "joint_accuracy_mean":float(vals.mean()),"run_sd":float(vals.std(ddof=1)) if len(vals)>1 else None,
                            "min_labeled_decisions":min(r['supervision']['labeled_decisions'] for r in selected),
                            "max_labeled_decisions":max(r['supervision']['labeled_decisions'] for r in selected)})
    report={"status":"completed_non_llm_controls","not_evidence_for_agent_learning":True,
            "source_audit":read_json(data_root/'audit.json'),"evaluation_split":split,
            "evaluation_policy":"Fixed prespecified baseline settings; no test-based hyperparameter selection",
            "budgets":list(budgets),"seeds":list(seeds),"runs":rows,"summary":summary}
    write_json(output_root/'baseline-results.json',report)
    return report
