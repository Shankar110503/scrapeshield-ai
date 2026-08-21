from __future__ import annotations

import os
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from .brightdata import BrightDataClient
from .healer import build_healing_prompt
from .models import add_demo_repair, normalize_records
from .monitor import inspect


st.set_page_config(
    page_title="ScrapeShield AI",
    page_icon="🛡️",
    layout="wide",
)


def secret_or_env(name: str, default: str = "") -> str:
    value = os.getenv(name, "")

    if value:
        return value

    try:
        value = st.secrets.get(name, default)
        return str(value) if value else default
    except Exception:
        return default


def demo_records() -> List[Dict[str, Any]]:
    return [
        {
            "product_name": "Laptop A",
            "price": "₹59,999",
            "stock": "In stock",
        },
        {
            "product_name": "Laptop B",
            "price": "₹74,999",
            "stock": "In stock",
        },
        {
            "product_name": "Laptop C",
            "price": "₹89,999",
            "stock": "Out of stock",
        },
    ]


def apply_css() -> None:
    st.markdown(
        """
        <style>
        .status-card {
            padding: 18px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.03);
        }
        .small {
            opacity: .70;
            font-size: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_css()

st.title("🛡️ ScrapeShield AI")
st.caption(
    "Self-healing web scraper reliability layer for the Into the Scrape-Verse hackathon."
)

token = secret_or_env("BRIGHT_DATA_API_TOKEN")
collector_id = secret_or_env("BRIGHT_DATA_COLLECTOR_ID")

real_mode = bool(token and collector_id)

# Session state keeps the last successful dataset visible after an action.
if "records" not in st.session_state:
    st.session_state.records = demo_records()

if "last_error" not in st.session_state:
    st.session_state.last_error = ""

if "collection_id" not in st.session_state:
    st.session_state.collection_id = ""

if "healing_result" not in st.session_state:
    st.session_state.healing_result = None

records = normalize_records(st.session_state.records)
status = inspect(records)

st.subheader("System Status")

c1, c2, c3, c4 = st.columns(4)

with c1:
    health_text = "HEALTHY" if status["healthy"] else "BROKEN"
    health_icon = "🟢" if status["healthy"] else "🔴"
    st.metric("Scraper Health", f"{health_icon} {health_text}")

with c2:
    st.metric("Rows", status["rows"])

with c3:
    st.metric("Missing Fields", len(status["missing_fields"]))

with c4:
    st.metric("Mode", "REAL" if real_mode else "DEMO")


st.divider()

st.header("🔄 Self-Healing Workflow")

steps = st.columns(4)

step_data = [
    ("1️⃣ Collect", "Bright Data collects structured data."),
    ("2️⃣ Detect", "ScrapeShield checks the output schema."),
    ("3️⃣ Heal", "Bright Data repairs broken extraction."),
    ("4️⃣ Recover", "Validated data continues downstream."),
]

for col, (title, description) in zip(steps, step_data):
    with col:
        st.subheader(title)
        st.caption(description)

url = st.text_input(
    "Public page URL",
    value="https://ecommerce-shop-brd.vercel.app/product/echo-portable-speaker",
)

b1, b2 = st.columns(2)

with b1:
    run_real = st.button(
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
        "BRIGHT_DATA_COLLECTOR_ID to run the real Bright Data collector."
    )

if run_real:
    st.session_state.last_error = ""

    try:
        client = BrightDataClient(
            token=token,
            collector=collector_id,
        )

        inputs = [{"url": url}]

        with st.spinner(
            "Bright Data collector is running. Waiting for the dataset..."
        ):
            data, collection_id = client.collect(
                inputs=inputs,
                timeout=600,
                poll_interval=5,
            )

        if not data:
            raise RuntimeError(
                "Bright Data finished but returned an empty dataset."
            )

        st.session_state.records = normalize_records(data)
        st.session_state.collection_id = collection_id

        st.success(
            f"Collector completed successfully. Collection ID: {collection_id}"
        )

        st.rerun()

    except Exception as exc:
        st.session_state.last_error = str(exc)

if simulate:
    # Start with a deliberately broken schema so the healing UI is demonstrable.
    broken = demo_records()
    for row in broken:
        row.pop("price", None)

    st.session_state.records = broken
    st.session_state.last_error = ""
    st.rerun()

if st.session_state.last_error:
    st.error(f"Collector failed: {st.session_state.last_error}")

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
    real_heal = st.button(
        "⚙ Self-Heal in Bright Data",
        use_container_width=True,
        disabled=not real_mode or status["healthy"],
    )

with h2:
    demo_heal = st.button(
        "⚡ Apply Demo Repair",
        use_container_width=True,
        disabled=status["healthy"],
    )

if real_heal:
    try:
        client = BrightDataClient(
            token=token,
            collector=collector_id,
        )

        with st.spinner("Sending self-healing instruction to Bright Data..."):
            result = client.self_heal(prompt)

        st.session_state.healing_result = result
        st.success("Self-healing instruction accepted by Bright Data.")

    except Exception as exc:
        st.error(f"Self-healing failed: {exc}")

if demo_heal:
    repaired = add_demo_repair(
        records,
        status["missing_fields"],
    )

    st.session_state.records = repaired
    st.session_state.last_error = ""
    st.success("Demo repair applied. Output schema is restored.")
    st.rerun()

if st.session_state.healing_result is not None:
    with st.expander("Bright Data self-healing response"):
        st.json(st.session_state.healing_result)


st.subheader("📊 Structured Output")

if records:
    st.dataframe(
        pd.DataFrame(records),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No structured records are available yet.")


st.divider()

with st.expander("🎬 Hackathon Demo Flow"):
    st.markdown(
        """
        **Collect → Detect → Heal → Recover**

        1. Collect structured product data.
        2. Detect missing schema fields.
        3. Ask Bright Data to self-heal the collector.
        4. Validate the repaired output before downstream use.

        The **Simulate Website Redesign** button intentionally removes
        `price` so the failure-detection and repair path can be demonstrated
        without making a real website change.
        """
    )

if st.session_state.collection_id:
    st.caption(
        f"Last Bright Data collection: {st.session_state.collection_id}"
    )

st.caption("ScrapeShield AI • Built for Into the Scrape-Verse 2026")
