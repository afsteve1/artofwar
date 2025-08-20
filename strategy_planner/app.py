from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

import streamlit as st

from storage import (
    init_db,
    list_canvases,
    get_canvas_by_id,
    get_canvas_by_name,
    save_canvas,
    delete_canvas,
    export_json,
    export_markdown,
)

APP_TITLE = "Strategy Planner — Value Proposition Canvas"


def _sanitize_filename(name: str) -> str:
    name = name.strip() or "untitled"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:60]


def load_canvas_into_state(canvas_id: int):
    data = get_canvas_by_id(canvas_id)
    if not data:
        return
    st.session_state["canvas_id"] = data["id"]
    st.session_state["canvas_name"] = data.get("name", "Untitled")
    st.session_state["customer_jobs"] = data.get("customer_jobs", "")
    st.session_state["pains"] = data.get("pains", "")
    st.session_state["gains"] = data.get("gains", "")
    st.session_state["products_services"] = data.get("products_services", "")
    st.session_state["gain_creators"] = data.get("gain_creators", "")
    st.session_state["pain_relievers"] = data.get("pain_relievers", "")
    st.session_state["last_loaded_name"] = data.get("name", "")


# Initialize
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
init_db()

# Sidebar: Canvas management
with st.sidebar:
    st.header("Canvases")

    # Load existing
    canvases = list_canvases()
    name_to_id = {c["name"]: c["id"] for c in canvases}
    options = ["— Select to Load —"] + list(name_to_id.keys())

    def on_select_change():
        selected = st.session_state.get("load_select")
        if selected and selected in name_to_id:
            load_canvas_into_state(name_to_id[selected])

    st.selectbox(
        "Load existing",
        options,
        index=0,
        key="load_select",
        on_change=on_select_change,
    )

    st.divider()

    # Create new / current name
    st.subheader("Current Canvas")
    name_val = st.text_input("Name", key="canvas_name", placeholder="e.g., SMB Field Technicians")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("New Canvas", use_container_width=True):
            st.session_state["canvas_id"] = None
            st.session_state["canvas_name"] = ""
            for k in [
                "customer_jobs",
                "pains",
                "gains",
                "products_services",
                "gain_creators",
                "pain_relievers",
            ]:
                st.session_state[k] = ""
            st.toast("Started a new canvas.")

    with col_b:
        if st.button("Save", type="primary", use_container_width=True):
            try:
                res = save_canvas(
                    canvas_id=st.session_state.get("canvas_id"),
                    name=st.session_state.get("canvas_name", "Untitled").strip() or "Untitled",
                    customer_jobs=st.session_state.get("customer_jobs", ""),
                    pains=st.session_state.get("pains", ""),
                    gains=st.session_state.get("gains", ""),
                    products_services=st.session_state.get("products_services", ""),
                    gain_creators=st.session_state.get("gain_creators", ""),
                    pain_relievers=st.session_state.get("pain_relievers", ""),
                )
                st.session_state["canvas_id"] = res["id"]
                st.session_state["last_loaded_name"] = res["name"]
                st.success("Saved.")
            except Exception as e:
                st.error(f"Save failed: {e}")

    # Delete
    disabled = st.session_state.get("canvas_id") is None
    confirm = st.checkbox("Confirm delete", value=False, disabled=disabled)
    if st.button("Delete", disabled=(disabled or not confirm), use_container_width=True):
        try:
            delete_canvas(st.session_state["canvas_id"])
            st.session_state["canvas_id"] = None
            st.session_state["canvas_name"] = ""
            for k in [
                "customer_jobs",
                "pains",
                "gains",
                "products_services",
                "gain_creators",
                "pain_relievers",
            ]:
                st.session_state[k] = ""
            st.success("Deleted.")
        except Exception as e:
            st.error(f"Delete failed: {e}")

    st.divider()

    # Export
    export_disabled = st.session_state.get("canvas_id") is None
    if not export_disabled:
        cid = int(st.session_state["canvas_id"])  # type: ignore
        json_bytes = export_json(cid).encode("utf-8")
        md_text = export_markdown(cid)
        fname_base = _sanitize_filename(st.session_state.get("canvas_name", "canvas"))
        st.download_button(
            "Download JSON",
            data=json_bytes,
            file_name=f"{fname_base}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "Download Markdown",
            data=md_text,
            file_name=f"{fname_base}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.info("Save first to enable exports.")

# Layout: Two columns for the canvas
left, right = st.columns(2)

with left:
    st.subheader("Customer Segment")
    st.text_area(
        "Customer Jobs",
        key="customer_jobs",
        height=160,
        placeholder="What tasks are customers trying to get done? Functional, social, personal, supporting jobs...",
    )
    st.text_area(
        "Pains",
        key="pains",
        height=160,
        placeholder="What annoys or prevents progress? Risks, bad outcomes, obstacles, costs...",
    )
    st.text_area(
        "Gains",
        key="gains",
        height=160,
        placeholder="What benefits do customers expect or desire? Required, expected, desired, unexpected...",
    )

with right:
    st.subheader("Value Proposition")
    st.text_area(
        "Products & Services",
        key="products_services",
        height=160,
        placeholder="What bundles of products/services help customers get a job done?",
    )
    st.text_area(
        "Gain Creators",
        key="gain_creators",
        height=160,
        placeholder="How does your offering create customer gains? Performance, cost, convenience...",
    )
    st.text_area(
        "Pain Relievers",
        key="pain_relievers",
        height=160,
        placeholder="How does your offering alleviate customer pains? Reduce risks, remove obstacles, lower costs...",
    )

st.caption(
    "Data stored locally in SQLite at 'strategy.db' next to this app. You can export JSON/Markdown anytime."
)
