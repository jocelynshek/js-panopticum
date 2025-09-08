#!/usr/bin/env python3
import json, re, csv, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# structure: [ { "topic": ..., "nodes": [...], "links": [...] }, ... ]
#INPUT = BASE_DIR.parent / "joc-data" / "networks.json"
INPUT = BASE_DIR / "cleaned_networks2.json"
OUTPUT = BASE_DIR / "overlap_candidates_revised.csv"

KEEP_BIGRAMS = True      # also compare 2-word phrases
MIN_OVERLAP = 1          # require at least this many shared tokens
MIN_TOKEN_LEN = 2
STOPWORDS = {
    "the","a","an","of","and","or","to","for","in","on","at","by","with",
    "said","say","says"
}

_word_chars = r"a-z0-9\-’'"

def normalize(text: str) -> str:
    t = text.lower()
    t = t.replace("’", "'").replace("“","\"").replace("”","\"")
    t = re.sub(rf"[^\s{_word_chars}]", " ", t)  # keep letters, digits, hyphen, apostrophe
    t = re.sub(r"\s+", " ", t).strip()
    return t

def tokenize(text: str):
    t = normalize(text)
    return [w for w in t.split() if len(w) >= MIN_TOKEN_LEN and w not in STOPWORDS]

def ngrams(tokens, n=2):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def token_set(text: str, keep_bigrams=KEEP_BIGRAMS):
    toks = tokenize(text)
    if keep_bigrams:
        toks += ngrams(toks, 2)
    return set(toks)

def load_links_any_shape(path: Path):
    raw = path.read_text(encoding="utf-8").strip()
    data = json.loads(raw)

    # Case A: top-level dict with "links"
    if isinstance(data, dict) and "links" in data and isinstance(data["links"], list):
        return data["links"]

    # Case B: top-level list of topics, each with "links"
    if isinstance(data, list):
        links = []
        for i, item in enumerate(data):
            maybe_links = item.get("links") if isinstance(item, dict) else None
            if isinstance(maybe_links, list):
                links.extend(maybe_links)
        if links:
            return links

    # Case C: already a flat list of edges
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        return data

    raise ValueError("Unrecognized JSON structure for networks.json")

def main():
    input_path = Path(INPUT)
    links = load_links_any_shape(input_path)

    out_rows = []
    for e in links:
        src = e.get("source")
        tgt = e.get("target")
        if not src or not tgt:
            # skip malformed
            continue

        val = e.get("value", 0)
        articles = e.get("shared_articles", []) or []

        src_set = token_set(src)
        tgt_set = token_set(tgt)
        overlap = sorted(src_set & tgt_set, key=lambda s: (-len(s.split()), s))  # phrases first

        if len(overlap) >= MIN_OVERLAP:
            out_rows.append({
                "source": src,
                "target": tgt,
                "value": val,
                "shared_articles_count": len(articles),
                "source_tokens": " | ".join(sorted(src_set)),
                "target_tokens": " | ".join(sorted(tgt_set)),
                "overlap_tokens": " | ".join(overlap),
                "overlap_count": len(overlap)
            })

    out_rows.sort(key=lambda r: (-r["overlap_count"], -r["value"],
                                 -r["shared_articles_count"], r["source"], r["target"]))

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        headers = ["source","target","value","shared_articles_count",
                   "source_tokens","target_tokens","overlap_tokens","overlap_count"]
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)

    print(f"Done. Wrote {len(out_rows)} overlapping edges to {OUTPUT}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        INPUT = Path(sys.argv[1])
    if len(sys.argv) > 2:
        OUTPUT = Path(sys.argv[2])
    main()
