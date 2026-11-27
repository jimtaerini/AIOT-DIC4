"""MITRE ATT&CK knowledge base (module ⑥): pinned Enterprise STIX bundle plus a small vector index.

The bundle is pinned to one release (data/attack/enterprise-attack-<version>.json) so
results are reproducible. Each active technique becomes one retrievable chunk whose
source reference is its technique ID (spec attack-mapping: every retrieved passage
carries its source). Revoked techniques map to their replacement through the bundle's
revoked-by relationships, which lets older labels (such as GUIDE's) be normalized to
the pinned version.

Embeddings come from the Gemini embedding API and are cached in
data/attack/embeddings_<version>_<model>.npz, so the index is built once (about
700 short documents).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

VERSION = "20.1"
DATA = Path("data/attack")
EMBED_MODEL = "gemini-embedding-001"
TECH_RE = re.compile(r"^T\d{4}(\.\d{3})?$")


def _ext_id(o: dict) -> str | None:
    for r in o.get("external_references", []):
        if r.get("source_name") == "mitre-attack":
            return r.get("external_id")
    return None


def _clean(text: str) -> str:
    text = re.sub(r"\(Citation:[^)]*\)", "", text or "")
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # markdown links -> link text
    return re.sub(r"\s+", " ", text).strip()


class AttackKB:
    def __init__(self, version: str = VERSION, path: Path | None = None):
        self.version = version
        bundle = json.loads((path or DATA / f"enterprise-attack-{version}.json").read_text())["objects"]
        by_stix = {o["id"]: o for o in bundle}
        self.tactic_names = {o["x_mitre_shortname"]: o["name"] for o in bundle if o["type"] == "x-mitre-tactic"}
        self.techniques: dict[str, dict] = {}
        self.revoked_to: dict[str, str] = {}
        self.deprecated: set[str] = set()
        revoked_stix = {}
        for o in bundle:
            if o["type"] != "attack-pattern":
                continue
            tid = _ext_id(o)
            if not tid:
                continue
            if o.get("revoked"):
                revoked_stix[o["id"]] = tid
                continue
            if o.get("x_mitre_deprecated"):
                self.deprecated.add(tid)
                continue
            self.techniques[tid] = {
                "id": tid, "name": o["name"],
                "tactics": sorted(p["phase_name"] for p in o.get("kill_chain_phases", [])
                                  if p.get("kill_chain_name") == "mitre-attack"),
                "description": _clean(o.get("description", "")),
            }
        for o in bundle:
            if o["type"] == "relationship" and o.get("relationship_type") == "revoked-by" \
                    and o["source_ref"] in revoked_stix:
                target = _ext_id(by_stix.get(o["target_ref"], {}))
                if target:
                    self.revoked_to[revoked_stix[o["source_ref"]]] = target
        for tid, t in self.techniques.items():  # sub-techniques get their parent's name for context
            if "." in tid and tid.split(".")[0] in self.techniques:
                t["full_name"] = f"{self.techniques[tid.split('.')[0]]['name']}: {t['name']}"
            else:
                t["full_name"] = t["name"]
        # mitigations (course-of-action) and the technique-specific guidance on each "mitigates" link
        self.mitigations: dict[str, dict] = {}
        coa_by_stix = {}
        for o in bundle:
            if o["type"] == "course-of-action" and not o.get("revoked") and not o.get("x_mitre_deprecated"):
                mid = _ext_id(o)
                if mid and mid.startswith("M"):
                    self.mitigations[mid] = {"id": mid, "name": o["name"], "description": _clean(o.get("description", ""))}
                    coa_by_stix[o["id"]] = mid
        tech_by_stix = {o["id"]: _ext_id(o) for o in bundle if o["type"] == "attack-pattern"}
        self.mitigations_of: dict[str, list[dict]] = {}
        for o in bundle:
            if o["type"] == "relationship" and o.get("relationship_type") == "mitigates" \
                    and o["source_ref"] in coa_by_stix and tech_by_stix.get(o["target_ref"]) in self.techniques:
                self.mitigations_of.setdefault(tech_by_stix[o["target_ref"]], []).append(
                    {"id": coa_by_stix[o["source_ref"]], "guidance": _clean(o.get("description", ""))})
        self.ids = sorted(self.techniques)
        self._emb = None

    # ----- label normalization -----
    def normalize(self, tid: str) -> str | None:
        """Map a technique ID to the pinned version: active as is, revoked to its
        replacement, deprecated / unknown (e.g. ICS T08xx) to None."""
        tid = tid.strip()
        for _ in range(5):  # follow revocation chains
            if tid in self.techniques:
                return tid
            if tid in self.revoked_to:
                tid = self.revoked_to[tid]
                continue
            return None
        return None

    def tactics_of(self, tids) -> set[str]:
        return {tac for t in tids if t in self.techniques for tac in self.techniques[t]["tactics"]}

    # ----- retrieval -----
    def document(self, tid: str, max_chars: int = 900) -> str:
        t = self.techniques[tid]
        return (f"{tid} {t['full_name']} (tactics: {', '.join(t['tactics'])}). "
                f"{t['description'][:max_chars]}")

    def _embeddings(self, client) -> np.ndarray:
        if self._emb is not None:
            return self._emb
        cache = DATA / f"embeddings_{self.version}_{EMBED_MODEL}.npz"
        if cache.exists():
            z = np.load(cache, allow_pickle=False)
            if list(z["ids"]) == self.ids:
                self._emb = z["emb"]
                return self._emb
        from google.genai import types
        vecs = []
        for i in range(0, len(self.ids), 50):
            batch = [self.document(t) for t in self.ids[i:i + 50]]
            r = client.models.embed_content(model=EMBED_MODEL, contents=batch,
                                            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
            vecs += [e.values for e in r.embeddings]
        emb = np.asarray(vecs, dtype=np.float32)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        np.savez(cache, ids=np.array(self.ids), emb=emb)
        self._emb = emb
        return emb

    def search(self, client, queries: list[str], k: int = 10) -> list[list[dict]]:
        """Top-k techniques per query by cosine similarity; each hit carries its source ID."""
        from google.genai import types
        emb = self._embeddings(client)
        vecs = []
        for i in range(0, len(queries), 50):
            r = client.models.embed_content(model=EMBED_MODEL, contents=queries[i:i + 50],
                                            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"))
            vecs += [e.values for e in r.embeddings]
        q = np.asarray(vecs, dtype=np.float32)
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        sims = q @ emb.T
        out = []
        for row in sims:
            top = np.argsort(-row)[:k]
            out.append([{"id": self.ids[j], "score": float(row[j]), "source": f"ATT&CK v{self.version} {self.ids[j]}"}
                        for j in top])
        return out
