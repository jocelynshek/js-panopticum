import json
import csv
from pathlib import Path
from collections import defaultdict

# ------------ CONFIG ------------
BASE_DIR = Path(__file__).resolve().parent
NETWORKS_PATH = BASE_DIR.parent.parent / "joc-data" / "networks.json"
MERGE_MAP_PATH = BASE_DIR / "merge_map.csv"
OUTPUT_PATH = BASE_DIR / "cleaned_networks2.json"

DROP_SELF_LOOPS = True
# ---------------------------------

def load_merge_map(path):
    mapping = {}
    if not path.exists():
        print(f"[WARNING] No merge_map.csv found at {path}. Proceeding without merges.")
        return mapping
    with open(path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_term = row["from_term"].strip()
            to_term = row["to_canonical"].strip()
            if from_term and to_term:
                mapping[from_term] = to_term
    return mapping

def canonicalize(label, merge_map):
    return merge_map.get(label, label)

# ------------ Load ------------
with open(NETWORKS_PATH, "r", encoding="utf-8") as f:
    networks = json.load(f)

merge_map = load_merge_map(MERGE_MAP_PATH)
cleaned_networks = []

# ------------ Process each topic ------------
for net in networks:
    topic = net.get("topic", None)

    # --- Canonicalize and merge nodes ---
    node_freq = defaultdict(int)
    node_group = {}

    for node in net["nodes"]:
        original = node["id"]
        canon = canonicalize(original, merge_map)
        node_freq[canon] += node.get("size", 1)
        node_group[canon] = node.get("group", 0)

    cleaned_nodes = [
        {"id": label, "size": size, "group": node_group.get(label, 0)}
        for label, size in node_freq.items()
    ]

    # --- Canonicalize and merge links ---
    link_weights = defaultdict(int)
    for link in net["links"]:
        s = canonicalize(link["source"], merge_map)
        t = canonicalize(link["target"], merge_map)

        if DROP_SELF_LOOPS and s == t:
            continue

        key = tuple(sorted([s, t]))  # undirected
        link_weights[key] += link.get("value", 1)

    cleaned_links = [
        {"source": a, "target": b, "value": w}
        for (a, b), w in link_weights.items()
    ]

    cleaned_networks.append({
        "topic": topic,
        "nodes": cleaned_nodes,
        "links": cleaned_links
    })

# ------------ Write output ------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(cleaned_networks, f, indent=2)

print(f"✅ Cleaned networks written to {OUTPUT_PATH.name}")
