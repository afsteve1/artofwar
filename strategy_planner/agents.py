from __future__ import annotations

import json
import os
from typing import Dict, Optional

import requests

try:
    import streamlit as st  # for st.secrets fallback
except Exception:  # pragma: no cover
    st = None  # type: ignore


def _get_secret(*keys: str) -> Optional[str]:
    # Look in Streamlit secrets then env
    for k in keys:
        if st is not None:
            try:
                v = st.secrets.get(k)  # type: ignore[attr-defined]
                if v:
                    return str(v)
            except Exception:
                pass
        v = os.environ.get(k)
        if v:
            return v
    return None


def run_agent(
    *,
    backend: str,
    model: str,
    system_prompt: str,
    user_input: str,
    context: Optional[Dict] = None,
    timeout: int = 60,
) -> str:
    backend = (backend or "").strip().lower()
    model = (model or "").strip()

    # Build a single prompt string that includes optional context
    ctx_text = ""
    if context:
        try:
            ctx_text = "\n\nCONTEXT (JSON):\n" + json.dumps(context, indent=2)
        except Exception:
            ctx_text = "\n\nCONTEXT: (unserializable)"

    # Route to appropriate backend handler
    if backend == "openai":
        api_key = _get_secret("OPENAI_API_KEY")
        if not api_key:
            return "[Error] OPENAI_API_KEY not set."
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input + ctx_text},
            ],
            "temperature": 0.3,
        }
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code != 200:
            return f"[OpenAI Error] {r.status_code}: {r.text[:500]}"
        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    elif backend == "anthropic":
        api_key = _get_secret("ANTHROPIC_API_KEY")
        if not api_key:
            return "[Error] ANTHROPIC_API_KEY not set."
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": model or "claude-3-5-sonnet-latest",
            "max_tokens": 1024,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_input + ctx_text}],
        }
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code != 200:
            return f"[Anthropic Error] {r.status_code}: {r.text[:500]}"
        data = r.json()
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")

    elif backend == "openrouter":
        api_key = _get_secret("OPENROUTER_API_KEY")
        if not api_key:
            return "[Error] OPENROUTER_API_KEY not set."
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model or "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input + ctx_text},
            ],
        }
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code != 200:
            return f"[OpenRouter Error] {r.status_code}: {r.text[:500]}"
        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    elif backend == "ollama":
        # Local Ollama server
        url = "http://localhost:11434/api/chat"
        body = {
            "model": model or "llama3.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input + ctx_text},
            ],
            "stream": False,
        }
        r = requests.post(url, json=body, timeout=timeout)
        if r.status_code != 200:
            return f"[Ollama Error] {r.status_code}: {r.text[:500]}"
        data = r.json()
        # Ollama returns a single message in 'message'
        msg = data.get("message", {})
        return msg.get("content", "")

    else:
        # Fallback: echo
        return "[Echo Backend]\n" + (user_input + ctx_text)
