"""Metered annotation access and paired nested adaptation trajectories."""
from __future__ import annotations
from dataclasses import dataclass, field
import copy
import json
import random
import math
from collections import Counter
import re
from pathlib import PurePosixPath

@dataclass
class BudgetLedger:
    limit: int
    revealed: set[str] = field(default_factory=set)
    events: list[dict] = field(default_factory=list)

    def reveal(self, record):
        ident = record["id"]
        if ident not in self.revealed and len(self.revealed) >= self.limit:
            raise ValueError("Gold annotation budget exhausted")
        is_new = ident not in self.revealed
        self.revealed.add(ident)
        self.events.append({"kind": "gold_reveal", "id": ident, "new": is_new,
                            "decisions": len(record["gold"]), "total_unique": len(self.revealed)})
        return copy.deepcopy(record)

    def summary(self):
        new = [x for x in self.events if x["new"]]
        return {"limit": self.limit, "unique_labeled_sentences": len(self.revealed),
                "labeled_decisions": sum(x["decisions"] for x in new), "reveal_calls": len(self.events)}

def trajectory(records, seed):
    rows = list(records)
    random.Random(seed).shuffle(rows)
    return rows

def safe_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(x in ("..", ".") for x in path.parts):
        raise ValueError("Only relative asset paths are allowed")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", name):
        raise ValueError("Invalid asset path")
    return str(path)

class AgentView:
    """Agent can access ONLY its materials, revealed examples and own assets.

    No raw data paths, evaluator, test gold, unrestricted host shell or API client
    objects are exposed to the model. Test workspaces are recreated per item.
    """
    def __init__(self, materials, revealed, assets=None, writable=False):
        self.materials = copy.deepcopy(materials)
        self.examples = copy.deepcopy(revealed)
        self.assets = copy.deepcopy(assets or {})
        self.writable = writable
        self.log = []

    def call(self, name, args):
        self.log.append({"tool": name, "arguments": copy.deepcopy(args)})
        if name == "list_materials":
            return {"guidelines": sorted(self.materials), "assets": sorted(self.assets), "examples": sorted(self.examples)}
        if name == "read_material":
            key = args["name"]
            if key not in self.materials and key not in self.assets:
                raise ValueError("Unknown authorized material")
            content = self.materials.get(key, self.assets.get(key))
            start = max(0, int(args.get("start", 0)))
            length = min(12000, max(1, int(args.get("length", 6000))))
            return {"name": key, "start": start, "text": content[start:start+length], "total_chars": len(content)}
        if name == "search_materials":
            def words(text):
                # PDF small caps: C OMPARISON R EF -> ComparisonRef.
                text=re.sub(r"\b[A-Z][A-Z ]{2,}[A-Z]\b",lambda m:m[0].replace(" ",""),text)
                return set(re.findall(r"[a-z]+",text.lower()))
            query=words(args["query"])
            chunks=[]
            for key, content in {**self.materials, **self.assets}.items():
                for start in range(0,len(content),800):
                    chunk=content[start:start+1200]
                    chunks.append((key,start,chunk,words(chunk)))
            df=Counter(w for _,_,_,ws in chunks for w in ws)
            ranked=[]
            for key,start,chunk,ws in chunks:
                overlap=query & ws
                if overlap:
                    score=sum(math.log(1+len(chunks)/(1+df[w])) for w in overlap)
                    ranked.append((score,key,start,chunk))
            ranked.sort(key=lambda x:(-x[0],x[1],x[2]))
            return [{"name":key,"start":start,"score":score,"text":chunk} for score,key,start,chunk in ranked[:5]]
        if name == "search_examples":
            query=set(re.findall(r"\w+",args["query"].lower()))
            limit=min(8,max(1,int(args.get("limit",3))))
            ranked=[]
            for key, example in self.examples.items():
                text=example["input"].get("text","")+" "+" ".join(t.get("text","") for t in example["input"].get("targets",[]))
                words=set(re.findall(r"\w+",text.lower()))
                score=len(query & words)/max(1,len(query | words))
                if key.lower()==args["query"].lower(): score=1.0
                if score>0: ranked.append((score,key))
            ranked.sort(key=lambda x:(-x[0],x[1]))
            return [{"similarity":score,"example":copy.deepcopy(self.examples[key])} for score,key in ranked[:limit]]
        if name == "read_example":
            if args["id"] not in self.examples:
                raise ValueError("Example has not been purchased")
            return copy.deepcopy(self.examples[args["id"]])
        if name == "write_asset":
            if not self.writable:
                raise ValueError("State is frozen during evaluation")
            path = safe_path(args["name"])
            content = args["text"]
            if not isinstance(content, str) or len(content) > 50000:
                raise ValueError("Asset too large or not text")
            self.assets[path] = content
            return {"written": path, "characters": len(content)}
        raise ValueError("Unauthorized tool")
