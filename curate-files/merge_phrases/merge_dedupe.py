import json
import csv
from pathlib import Path
from collections import defaultdict, Counter

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

def most_common(lst):
    return Counter(lst).most_common(1)[0][0] if lst else 0

# ------------ Load ------------
with open(NETWORKS_PATH, "r", encoding="utf-8") as f:
    networks = json.load(f)

merge_map = load_merge_map(MERGE_MAP_PATH)
cleaned_networks = []

# ------------ Process each topic ------------
for net in networks:
    topic = net.get("topic", None)

    # --- Canonicalize and merge nodes ---
    node_sizes = defaultdict(int)
    node_groups = defaultdict(list)
    node_categories = defaultdict(list)

    for node in net["nodes"]:
        original = node["id"]
        canon = canonicalize(original, merge_map)
        node_sizes[canon] += node.get("size", 1)
        node_groups[canon].append(node.get("group", 0))
        node_categories[canon].append(node.get("category", "Other"))
    
    def most_common(lst):
        return Counter(lst).most_common(1)[0][0] if lst else "Other"

    cleaned_nodes = [
        {"id": label,
         "size": node_sizes[label],
         "group": most_common(node_groups[label]),
         "category": most_common(node_categories[label])}
        for label in node_sizes
    ]

    # --- Canonicalize and merge links ---
    link_bucket = defaultdict(lambda: {"shared_articles": set()})

    for link in net["links"]:
        s = canonicalize(link["source"], merge_map)
        t = canonicalize(link["target"], merge_map)

        if DROP_SELF_LOOPS and s == t:
            continue

        key = tuple(sorted([s, t]))  # undirected
        link_bucket[key]["shared_articles"].update(link.get("shared_articles", []) or [])

    cleaned_links = [
        {
            "source": a,
            "target": b,
            "value": len(shared := sorted(data["shared_articles"])),
            "shared_articles": shared
        }
        for (a, b), data in link_bucket.items()
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
