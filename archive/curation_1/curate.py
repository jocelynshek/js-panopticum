import streamlit as st
import json
from pathlib import Path
import streamlit.components.v1 as components

# --- Paths ---
network_path = Path("networks2.json")
output_path = Path("curated_phrases.json")

# --- Load data ---
with network_path.open() as f:
    networks = json.load(f)

if output_path.exists():
    try:
        with output_path.open() as f:
            curated = json.load(f)
    except json.JSONDecodeError:
        curated = {}
else:
    curated = {}

# --- Sidebar: select topic ---
topic_ids = [n["topic"] for n in networks]
selected_topic = st.sidebar.selectbox("Select a topic ID", topic_ids)

# Reset index if switching topics
if "previous_topic" not in st.session_state:
    st.session_state.previous_topic = selected_topic
if st.session_state.previous_topic != selected_topic:
    st.session_state.index = 0
    st.session_state.previous_topic = selected_topic

# Get phrases for this topic
topic_net = next(n for n in networks if n["topic"] == selected_topic)
phrases = sorted([n["id"] for n in topic_net["nodes"]], key=lambda x: -len(x))

# Index tracking
if "index" not in st.session_state:
    st.session_state.index = 0
st.session_state.index = min(st.session_state.index, len(phrases) - 1)

# Navigation buttons
st.sidebar.button("⬅️ Prev", on_click=lambda: st.session_state.update(index=max(0, st.session_state.index - 1)))
st.sidebar.button("➡️ Next", on_click=lambda: st.session_state.update(index=min(len(phrases)-1, st.session_state.index + 1)))

# Current phrase
if phrases:
    curr_phrase = phrases[st.session_state.index]
    st.write(f"### Topic {selected_topic} — Phrase {st.session_state.index+1} of {len(phrases)}")
    st.markdown(f"**Phrase:** `{curr_phrase}`")

    # Inputs
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        keep = st.button("✅ Keep", key="keep_button")
    with col2:
        reject = st.button("❌ Reject", key="reject_button")
    with col3:
        merge = st.text_input("🔁 Merge with (optional)", key="merge_input")

    # Save decision
    if keep or reject:
        curated.setdefault(str(selected_topic), {})
        curated[str(selected_topic)][curr_phrase] = {
            "action": "keep" if keep else "remove",
            "merge_to": merge if merge else None
        }
        with output_path.open("w") as f:
            json.dump(curated, f, indent=2)

        # Move to the next phrase and rerun cleanly
        st.session_state.index += 1
        st.rerun()


    # Keyboard shortcut hint
    st.caption("⬅️ = Reject | ➡️ = Keep | Optional: merge manually")

    # Inject keyboard shortcuts
    components.html("""
        <script>
        const doc = window.parent.document;
        doc.addEventListener("keydown", function(e) {
            if (e.key === "ArrowRight") {
                const btn = doc.querySelector('[data-testid="stButton"] [aria-label="✅ Keep"]');
                if (btn) btn.click();
            }
            if (e.key === "ArrowLeft") {
                const btn = doc.querySelector('[data-testid="stButton"] [aria-label="❌ Reject"]');
                if (btn) btn.click();
            }
        });
        </script>
    """, height=0)

# Show current progress
if str(selected_topic) in curated:
    st.markdown("### 🗂️ Curated so far:")
    for phrase, decision in curated[str(selected_topic)].items():
        st.write(f"• `{phrase}` → **{decision['action']}**" +
                 (f" → `{decision['merge_to']}`" if decision['merge_to'] else ""))
