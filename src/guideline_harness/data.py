"""Trusted preparation. Raw annotations never enter the model's filesystem view."""
from __future__ import annotations
import hashlib
import json
import urllib.request
from pathlib import Path
from .ontology import SNACS_LABELS

STREUSLE_COMMIT = "8ba61fe4f216e7967500a862554a4fff79d25f5d"

def read_json(path):
    return json.loads(Path(path).read_text())

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def fetch_streusle(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"repository": "nert-nlp/streusle", "commit": STREUSLE_COMMIT, "files": []}
    paths = {s + ".json": f"{s}/streusle.ud_{s}.json" for s in ("train", "dev", "test")}
    paths.update({"LICENSE.txt": "LICENSE.txt", "README.md": "README.md", "supersenses.py": "supersenses.py"})
    for name, relative in paths.items():
        url = f"https://raw.githubusercontent.com/nert-nlp/streusle/{STREUSLE_COMMIT}/{relative}"
        with urllib.request.urlopen(url, timeout=90) as response:
            contents = response.read()
        (root / name).write_bytes(contents)
        manifest["files"].append({"file": name, "url": url, "sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents)})
    write_json(root / "manifest.json", manifest)
    return manifest

def project_snacs(sentence):
    """Given-target SNACS. Do not expose POS, syntax, MISC or any semantic gold."""
    targets, gold, ignored = [], {}, 0
    for column in ("swes", "smwes"):
        for key, expression in sentence[column].items():
            role, function = expression.get("ss"), expression.get("ss2")
            if role == "??" and expression.get("lexcat") in {"P", "PP", "POSS"}:
                ignored += 1
                continue
            if not isinstance(role, str) or not role.startswith("p."):
                continue
            if role == "p.??" or function == "p.??" or not function:
                ignored += 1
                continue
            target_id = f"{column}:{key}"
            positions = expression["toknums"]
            targets.append({"id": target_id, "token_indices": positions,
                            "text": " ".join(sentence["toks"][i - 1]["word"] for i in positions)})
            gold[target_id] = [role, function]
    if not targets:
        return None, ignored
    sid = sentence["sent_id"]
    return {"id": sid, "group": sid.rsplit("-", 1)[0], "input": {
        "text": sentence["text"], "tokens": [t["word"] for t in sentence["toks"]], "targets": targets},
        "gold": gold}, ignored

def prepare_snacs(raw_root, output_root):
    raw_root, output_root = Path(raw_root), Path(output_root)
    source_manifest = read_json(raw_root / "manifest.json")
    if source_manifest["commit"] != STREUSLE_COMMIT:
        raise ValueError("Unexpected source version")
    for entry in source_manifest["files"]:
        if hashlib.sha256((raw_root / entry["file"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Source checksum mismatch: {entry['file']}")
    stats, sets = {}, {}
    labels = set()
    for split in ("train", "dev", "test"):
        rows, excluded = [], 0
        source = read_json(raw_root / f"{split}.json")
        for sentence in source:
            record, ignored = project_snacs(sentence)
            excluded += ignored
            if record:
                rows.append(record)
                if split == "train":
                    labels.update(x for pair in record["gold"].values() for x in pair)
        groups = {row["group"] for row in rows}
        sets[split] = groups
        write_json(output_root / "private" / f"{split}.json", rows)
        # Only IDs and authorized unlabeled fields may be exposed via controller.
        write_json(output_root / "public" / f"{split}.json", [{k:v for k,v in r.items() if k != "gold"} for r in rows])
        stats[split] = {"source_sentences": len(source), "sentences_with_targets": len(rows),
                        "documents": len(groups), "target_decisions": sum(len(r["gold"]) for r in rows),
                        "excluded_uncertain_or_missing_function": excluded,
                        "input_sha256": digest([{k:v for k,v in r.items() if k != 'gold'} for r in rows])}
    for a,b in (("train","dev"),("train","test"),("dev","test")):
        overlap = sets[a] & sets[b]
        if overlap:
            raise ValueError(f"Document overlap {a}/{b}: {sorted(overlap)}")
    stats["source_commit"] = STREUSLE_COMMIT
    stats["track"] = "given-target SNACS, joint scene-role/lexical-function classification"
    stats["budget_unit"] = "one sentence; reveals all retained SNACS targets in that sentence"
    stats["additional_supervision"] = "gold target boundaries supplied to every condition"
    stats["labels_seen_in_train"] = sorted(labels)
    stats["label_inventory"] = sorted(SNACS_LABELS)
    write_json(output_root / "audit.json", stats)
    return stats
