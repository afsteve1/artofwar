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
    list_agents,
    get_agent_by_id,
    get_agent_by_name,
    save_agent,
    delete_agent,
)
from agents import run_agent

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


def load_agent_into_state(agent_id: int):
    data = get_agent_by_id(agent_id)
    if not data:
        return
    st.session_state["agent_id"] = data["id"]
    st.session_state["agent_name"] = data.get("name", "")
    st.session_state["agent_function"] = data.get("function", "")
    st.session_state["agent_prompt"] = data.get("prompt", "")
    st.session_state["agent_backend"] = data.get("backend", "")
    st.session_state["agent_model"] = data.get("model", "")


# Initialize
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
init_db()

# Session state init
if "run_history" not in st.session_state:
    st.session_state["run_history"] = []

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

    st.divider()

    # Agents quick tip
    st.header("Agents")
    st.info("Manage agents in the Agents tab. Then use the Run tab to execute.")

tab_canvas, tab_agents, tab_run = st.tabs(["Canvas", "Agents", "Run"])

with tab_canvas:
    # Layout: Two columns for the canvas
    left, right = st.columns(2)

    with left:
        st.subheader("Customer Segment")
        st.text_area(
            "Customer Jobs",
            key="customer_jobs",
            height=160,
            placeholder="What tasks are customers trying to get done? Functional, social, personal, supporting jobs...",
            help="Describe what your customer is trying to accomplish."
        )
        st.text_area(
            "Pains",
            key="pains",
            height=160,
            placeholder="What annoys or prevents progress? Risks, bad outcomes, obstacles, costs...",
            help="List the negative outcomes, obstacles, and risks."
        )
        st.text_area(
            "Gains",
            key="gains",
            height=160,
            placeholder="What benefits do customers expect or desire? Required, expected, desired, unexpected...",
            help="List benefits your customer expects, desires, or would be surprised by."
        )

    with right:
        st.subheader("Value Proposition")
        st.text_area(
            "Products & Services",
            key="products_services",
            height=160,
            placeholder="What bundles of products/services help customers get a job done?",
            help="Your offering that addresses customer jobs."
        )
        st.text_area(
            "Gain Creators",
            key="gain_creators",
            height=160,
            placeholder="How does your offering create customer gains? Performance, cost, convenience...",
            help="Explain how your offering produces outcomes customers want."
        )
        st.text_area(
            "Pain Relievers",
            key="pain_relievers",
            height=160,
            placeholder="How does your offering alleviate customer pains? Reduce risks, remove obstacles, lower costs...",
            help="Explain how your offering reduces or eliminates customer pains."
        )

    st.caption(
        "Data stored locally in SQLite at 'strategy.db'. Use the sidebar to Load/New/Save/Delete or Export."
    )

with tab_agents:
    st.subheader("Manage Agents")
    agents_all = list_agents()
    # Filter/search
    search_q = st.text_input("Search agents", key="agent_search_tab", placeholder="Type to filter by name")
    if search_q:
        agents_filtered = [a for a in agents_all if search_q.lower() in a["name"].lower()]
    else:
        agents_filtered = agents_all

    col_list, col_form = st.columns([1, 2], gap="large")

    with col_list:
        st.markdown("**Existing Agents**")
        names = [a["name"] for a in agents_filtered]
        name_to_id_tab = {a["name"]: a["id"] for a in agents_filtered}
        options_tab = ["— Select —"] + names

        def on_agent_select_tab_change():
            selected = st.session_state.get("load_agent_select_tab")
            if selected and selected in name_to_id_tab:
                load_agent_into_state(name_to_id_tab[selected])

        st.selectbox(
            "Load agent",
            options_tab,
            index=0,
            key="load_agent_select_tab",
            on_change=on_agent_select_tab_change,
        )

        if st.session_state.get("agent_name"):
            if st.button("Use this agent in Run tab", use_container_width=True):
                st.session_state["run_agent_select"] = st.session_state.get("agent_name")
                st.toast("Agent pre-selected in Run tab.")

    with col_form:
        st.markdown("**Current Agent**")
        st.text_input("Name", key="agent_name", placeholder="e.g., Market Researcher")
        st.text_input("Function (role)", key="agent_function", placeholder="What this agent does")
        st.text_area("Prompt (guidance)", key="agent_prompt", height=160, placeholder="Detailed instructions for the agent")
        st.selectbox("Backend", ["openai", "anthropic", "openrouter", "ollama", "echo"], key="agent_backend")
        st.text_input("Model", key="agent_model", placeholder="e.g., gpt-4o-mini, claude-3-5-sonnet, llama3.1")

        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("New", use_container_width=True):
                st.session_state["agent_id"] = None
                st.session_state["agent_name"] = ""
                st.session_state["agent_function"] = ""
                st.session_state["agent_prompt"] = ""
                st.session_state["agent_backend"] = "openai"
                st.session_state["agent_model"] = ""
                st.toast("Started a new agent.")
        with c2:
            if st.button("Save", type="primary", use_container_width=True):
                try:
                    res = save_agent(
                        agent_id=st.session_state.get("agent_id"),
                        name=st.session_state.get("agent_name", "Untitled Agent").strip() or "Untitled Agent",
                        function=st.session_state.get("agent_function", ""),
                        prompt=st.session_state.get("agent_prompt", ""),
                        backend=st.session_state.get("agent_backend", ""),
                        model=st.session_state.get("agent_model", ""),
                    )
                    st.session_state["agent_id"] = res["id"]
                    st.success("Agent saved.")
                except Exception as e:
                    st.error(f"Save failed: {e}")
        with c3:
            a_disabled_tab = st.session_state.get("agent_id") is None
            if st.button("Delete", disabled=a_disabled_tab, use_container_width=True):
                try:
                    delete_agent(st.session_state["agent_id"])
                    st.session_state["agent_id"] = None
                    st.session_state["agent_name"] = ""
                    st.session_state["agent_function"] = ""
                    st.session_state["agent_prompt"] = ""
                    st.session_state["agent_backend"] = "openai"
                    st.session_state["agent_model"] = ""
                    st.success("Agent deleted.")
                except Exception as e:
                    st.error(f"Delete failed: {e}")

    st.caption("Tip: Save agents with clear names and roles. Use the Run tab to execute them on tasks.")

with tab_run:
    st.subheader("Run an Agent against this canvas or a custom task")
    # Prepare agent selection
    agents_for_run = list_agents()
    run_agent_map = {a["name"]: a for a in agents_for_run}
    run_options = ["— Select an Agent —"] + list(run_agent_map.keys())
    selected_run_name = st.selectbox("Agent to run", run_options, index=0, key="run_agent_select")

    with st.expander("Options", expanded=True):
        include_ctx = st.checkbox("Include current canvas as context", value=True)
        user_input = st.text_area(
            "Task input",
            key="run_user_input",
            height=120,
            placeholder="Describe the task (e.g., Generate 5 customer interview questions for the current canvas)",
        )

    run_col1, run_col2 = st.columns([1, 3])
    with run_col1:
        run_clicked = st.button("Run", type="primary")
    with run_col2:
        out_placeholder = st.empty()

    if run_clicked:
        if selected_run_name not in run_agent_map:
            st.warning("Select an agent first.")
        elif not user_input.strip():
            st.warning("Enter a task input.")
        else:
            a = run_agent_map[selected_run_name]
            system_prompt = (a.get("function") or "").strip()
            if st.session_state.get("agent_prompt") and a.get("name") == st.session_state.get("agent_name"):
                # If the agent loaded in sidebar matches, use its prompt from state (which may be edited)
                agent_prompt_text = st.session_state.get("agent_prompt", "")
            else:
                # Fetch full agent to get prompt
                full = get_agent_by_id(int(a["id"]))
                agent_prompt_text = (full or {}).get("prompt", "")

            sys_full = ("Role: " + system_prompt + "\n\nInstructions: " + agent_prompt_text).strip() or "You are a helpful strategy assistant."

            context = None
            if include_ctx:
                context = {
                    "canvas": {
                        "name": st.session_state.get("canvas_name"),
                        "customer_jobs": st.session_state.get("customer_jobs"),
                        "pains": st.session_state.get("pains"),
                        "gains": st.session_state.get("gains"),
                        "products_services": st.session_state.get("products_services"),
                        "gain_creators": st.session_state.get("gain_creators"),
                        "pain_relievers": st.session_state.get("pain_relievers"),
                    }
                }

            with st.spinner("Running agent..."):
                output = run_agent(
                    backend=a.get("backend", "echo"),
                    model=a.get("model", ""),
                    system_prompt=sys_full,
                    user_input=user_input,
                    context=context,
                )

            # Show output and store
            out_text = output or "(no output)"
            out_placeholder.markdown(out_text)
            st.session_state["last_run_output"] = out_text
            st.session_state["run_history"].append(
                {
                    "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "agent": a.get("name", "(unknown)"),
                    "input": user_input,
                    "output": out_text,
                }
            )

    # Actions and history
    if st.session_state.get("last_run_output"):
        file_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "Download last output",
            data=st.session_state["last_run_output"],
            file_name=f"agent_output_{file_ts}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with st.expander("History"):
        if not st.session_state.get("run_history"):
            st.write("No runs yet.")
        else:
            for item in st.session_state["run_history"][-20:]:  # last 20
                st.markdown(f"**{item['ts']} — {item['agent']}**")
                st.markdown(f"Task: {item['input']}")
                st.markdown(item["output"]) 
            if st.button("Clear history"):
                st.session_state["run_history"] = []
                st.session_state["last_run_output"] = ""
