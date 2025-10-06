import json
from pathlib import Path
import networkx as nx
from collections import defaultdict, Counter

from networkx.algorithms.community import greedy_modularity_communities

# ------------ CONFIG ------------
BASE_DIR = Path(__file__).resolve().parent
NETWORKS_PATH = BASE_DIR / "cleaned_networks2.json"
OUTPUT_PATH = BASE_DIR / "topic_clusters2.json"

NUM_LABEL_TERMS = 3  # How many top phrases to use for naming clusters
# ---------------------------------

with open(NETWORKS_PATH, "r", encoding="utf-8") as f:
    networks = json.load(f)

all_topic_clusters = []

for net in networks:
    topic_id = net["topic"]
    nodes = {n["id"]: n for n in net["nodes"]}
    links = net["links"]

    # Build graph
    G = nx.Graph()
    for node_id in nodes:
        G.add_node(node_id, size=nodes[node_id]["size"])
    for link in links:
        G.add_edge(link["source"], link["target"], weight=link["value"])

    # Community detection
    communities = list(greedy_modularity_communities(G))

    clusters = []
    for comm in communities:
        phrases = list(comm)
        # Sort by node size (importance)
        phrases.sort(key=lambda p: nodes[p]["size"], reverse=True)

        # Use top N phrases as label
        label = ", ".join(phrases[:NUM_LABEL_TERMS])
        clusters.append({
            "label": label,
            "phrases": phrases
        })

    all_topic_clusters.append({
        "topic": topic_id,
        "clusters": clusters
    })

# Save result
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(all_topic_clusters, f, indent=2)

print(f"✅ Wrote topic cluster structure to {OUTPUT_PATH}")
