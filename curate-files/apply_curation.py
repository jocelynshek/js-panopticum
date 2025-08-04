import json
from pathlib import Path
from collections import defaultdict

# Load original networks and curated phrase decisions
with open("networks2.json") as f:
    networks = json.load(f)

with open("curated_phrases.json") as f:
    curated = json.load(f)

# Cleaned network output
cleaned_networks = []

for net in networks:
    topic_id = str(net["topic"])
    decisions = curated.get(topic_id, {})

    phrase_map = {}  # Maps old phrase to canonical phrase (merged or kept)

    for node in net["nodes"]:
        phrase = node["id"]
        decision = decisions.get(phrase)

        if not decision:
            continue  # if not curated, skip the phrase (conservative)

        if decision["action"] == "remove":
            continue  # exclude
        elif decision["action"] == "keep":
            phrase_map[phrase] = phrase
        elif decision["action"] == "keep" and decision["merge_to"]:
            phrase_map[phrase] = decision["merge_to"]
        elif decision["action"] == "remove" and decision["merge_to"]:
            phrase_map[phrase] = decision["merge_to"]

    # Build new frequency-counted nodes
    node_freq = defaultdict(int)
    node_group = {}
    for node in net["nodes"]:
        old = node["id"]
        new = phrase_map.get(old)
        if new:
            node_freq[new] += node["size"]
            node_group[new] = node["group"]

    cleaned_nodes = [
        {"id": phrase, "size": size, "group": node_group.get(phrase, 0)}
        for phrase, size in node_freq.items()
    ]

    # Build new links
    link_weights = defaultdict(int)
    for link in net["links"]:
        src = phrase_map.get(link["source"])
        tgt = phrase_map.get(link["target"])

        if not src or not tgt or src == tgt:
            continue  # skip removed or self-loops

        key = tuple(sorted([src, tgt]))
        link_weights[key] += link["value"]

    cleaned_links = [
        {"source": a, "target": b, "value": w}
        for (a, b), w in link_weights.items()
    ]

    cleaned_networks.append({
        "topic": net["topic"],
        "nodes": cleaned_nodes,
        "links": cleaned_links
    })

# Save new network for web app
with open("cleaned_networks.json", "w") as f:
    json.dump(cleaned_networks, f, indent=2)

print("✅ Saved cleaned networks to cleaned_networks.json")
