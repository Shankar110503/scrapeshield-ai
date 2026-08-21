from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

# Make the repository root importable on Streamlit Cloud.
# This avoids the ImportError caused by `from .brightdata ...`
# when dashboard.py is launched as the Streamlit main script.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.brightdata import BrightDataClient
from app.healer import build_healing_prompt
from app.models import add_demo_repair, normalize_records
from app.monitor import inspect


st.set_page_config(
    page_title="ScrapeShield AI",
    page_icon="🛡️",
    layout="wide",
)


def get_secret(name: str) -> str:
    value = os.getenv(name, "")
    if value:
        return value

    try:
        value = st.secrets.get(name, "")
        return str(value or "")
    except Exception:
        return ""


def demo_records() -> List[Dict[str, Any]]:
    return [
        {"product_name": "Laptop A", "price": "₹59,999", "stock": "In stock"},
        {"product_name": "Laptop B", "price": "₹74,999", "stock": "In stock"},
        {"product_name": "Laptop C", "price": "₹89,999", "stock": "Out of stock"},
    ]


st.title("🛡️ ScrapeShield AI")
st.caption(
    "Self-healing web scraper reliability layer for the Into the Scrape-Verse hackathon."
)

token = get_secret("BRIGHT_DATA_API_TOKEN")
collector = get_secret("BRIGHT_DATA_COLLECTOR_ID")
real_mode = bool(token and collector)

if "records" not in st.session_state:
    st.session_state.records = demo_records()

if "error" not in st.session_state:
    st.session_state.error = ""

if "collection_id" not in st.session_state:
    st.session_state.collection_id = ""

records = normalize_records(st.session_state.records)
status = inspect(records)

st.subheader("System Status")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Scraper Health",
        ("🟢 HEALTHY" if status["healthy"] else "🔴 BROKEN"),
    )

with c2:
    st.metric("Rows", status["rows"])

with c3:
    st.metric("Missing Fields", len(status["missing_fields"]))

with c4:
    st.metric("Mode", "REAL" if real_mode else "DEMO")

st.divider()

st.header("🔄 Self-Healing Workflow")

s1, s2, s3, s4 = st.columns(4)

with s1:
    st.subheader("1️⃣ Collect")
    st.caption("Bright Data collects structured data.")

with s2:
    st.subheader("2️⃣ Detect")
    st.caption("ScrapeShield checks the output schema.")

with s3:
    st.subheader("3️⃣ Heal")
    st.caption("Bright Data repairs broken extraction.")

with s4:
    st.subheader("4️⃣ Recover")
    st.caption("Validated data continues downstream.")

url = st.text_input(
    "Public page URL",
    "https://ecommerce-shop-brd.vercel.app/product/echo-portable-speaker",
)

b1, b2 = st.columns(2)

with b1:
    run = st.button(
        "▶ Run Bright Data Collector",
        use_container_width=True,
        disabled=not real_mode,
    )

with b2:
    simulate = st.button(
        "🛠️ Simulate Website Redesign",
        use_container_width=True,
    )

if not real_mode:
    st.warning(
        "Demo mode is active. Add BRIGHT_DATA_API_TOKEN and "
        "BRIGHT_DATA_COLLECTOR_ID in Streamlit Secrets for REAL mode."
    )

if run:
    st.session_state.error = ""

    try:
        client = BrightDataClient(
            token=token,
            collector=collector,
        )

        with st.spinner(
            "Collector is running. Waiting for Bright Data dataset..."
        ):
            data, collection_id = client.collect(
                [{"url": url}],
                timeout=600,
                poll_interval=5,
            )

        if not data:
            raise RuntimeError("Bright Data returned an empty dataset.")

        st.session_state.records = normalize_records(data)
        st.session_state.collection_id = collection_id
        st.success("Bright Data collection completed.")
        st.rerun()

    except Exception as exc:
        st.session_state.error = str(exc)

if simulate:
    broken = demo_records()

    for row in broken:
        row.pop("price", None)

    st.session_state.records = broken
    st.session_state.error = ""
    st.rerun()

if st.session_state.error:
    st.error(f"Collector failed: {st.session_state.error}")

records = normalize_records(st.session_state.records)
status = inspect(records)

if status["healthy"]:
    st.success("✅ Extraction healthy. All required fields are present.")
else:
    st.error(
        "🚨 Extraction failure detected. Missing fields: "
        + ", ".join(status["missing_fields"])
    )

st.subheader("🔎 Failure Detection")

if status["healthy"]:
    st.write(
        "ScrapeShield detected that the expected output schema is satisfied."
    )
else:
    st.write(
        "ScrapeShield detected that the expected output schema is no longer being satisfied."
    )
    st.write("**Missing fields:**")
    for field in status["missing_fields"]:
        st.warning(field)

st.subheader("🧿 Self-Healing Instruction")

prompt = build_healing_prompt(status["missing_fields"])
st.code(prompt, language="text")

h1, h2 = st.columns(2)

with h1:
    heal = st.button(
        "⚙ Self-Heal in Bright Data",
        use_container_width=True,
        disabled=not real_mode or status["healthy"],
    )

with h2:
    repair = st.button(
        "⚡ Apply Demo Repair",
        use_container_width=True,
        disabled=status["healthy"],
    )

if heal:
    try:
        client = BrightDataClient(
            token=token,
            collector=collector,
        )

        with st.spinner("Sending self-healing instruction..."):
            result = client.self_heal(prompt)

        st.success("Self-healing request accepted by Bright Data.")

        with st.expander("Bright Data response"):
            st.json(result)

    except Exception as exc:
        st.error(f"Self-healing failed: {exc}")

if repair:
    st.session_state.records = add_demo_repair(
        records,
        status["missing_fields"],
    )
    st.session_state.error = ""
    st.rerun()

st.subheader("📊 Structured Output")

if records:
    st.dataframe(
        pd.DataFrame(records),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No structured records available.")

st.divider()

with st.expander("🎬 Hackathon Demo Flow"):
    st.markdown(
        """
        **Collect → Detect → Heal → Recover**

        The **Simulate Website Redesign** button intentionally removes
        the `price` field. ScrapeShield detects the schema failure and
        can restore the missing field in demo mode.

        In REAL mode, Bright Data is used for collection and
        self-healing.
        """
    )

if st.session_state.collection_id:
    st.caption(
        f"Last Bright Data collection: {st.session_state.collection_id}"
    )

st.caption("ScrapeShield AI • Built for Into the Scrape-Verse 2026")
