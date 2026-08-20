import os
import sys
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv


# Make imports work when Streamlit runs:
# streamlit run app/dashboard.py
APP_DIR = os.path.dirname(os.path.abspath(__file__))

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


from models import FieldSpec
from monitor import check_health
from healer import demo_repair


load_dotenv()


st.set_page_config(
    page_title="ScrapeShield AI",
    page_icon="🛡️",
    layout="wide",
)


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------

st.title("🛡️ ScrapeShield AI")

st.caption(
    "Self-healing web scraper reliability layer "
    "for the Into the Scrape-Verse hackathon."
)


# ---------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------

schema = [
    FieldSpec(
        name="product_name",
        description="Product name",
    ),
    FieldSpec(
        name="price",
        description="Current price",
    ),
    FieldSpec(
        name="stock",
        description="Availability",
    ),
]


# ---------------------------------------------------------
# DEMO DATA
# ---------------------------------------------------------

healthy_rows: List[Dict[str, Any]] = [
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


broken_rows: List[Dict[str, Any]] = [
    {
        "product_name": "Laptop A",
        "stock": "In stock",
        "_recovered_price": "₹59,999",
    },
    {
        "product_name": "Laptop B",
        "stock": "In stock",
        "_recovered_price": "₹74,999",
    },
    {
        "product_name": "Laptop C",
        "stock": "Out of stock",
        "_recovered_price": "₹89,999",
    },
]


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "rows" not in st.session_state:
    st.session_state.rows = healthy_rows

if "stage" not in st.session_state:
    st.session_state.stage = "HEALTHY"

if "snapshot" not in st.session_state:
    st.session_state.snapshot = None

if "last_heal_result" not in st.session_state:
    st.session_state.last_heal_result = None


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

health = check_health(
    st.session_state.rows,
    schema,
)


real_mode = bool(
    os.getenv("BRIGHT_DATA_API_TOKEN")
    and os.getenv("BRIGHT_DATA_COLLECTOR_ID")
)


# ---------------------------------------------------------
# STATUS
# ---------------------------------------------------------

if health.healthy:
    status_text = "🟢 HEALTHY"
else:
    status_text = "🔴 BROKEN"


st.subheader("System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Scraper Health",
        status_text,
    )

with col2:
    st.metric(
        "Rows",
        health.row_count,
    )

with col3:
    st.metric(
        "Missing Fields",
        len(health.missing_fields),
    )

with col4:
    st.metric(
        "Mode",
        "REAL" if real_mode else "DEMO",
    )


# ---------------------------------------------------------
# WORKFLOW
# ---------------------------------------------------------

st.divider()

st.subheader("🔄 Self-Healing Workflow")

workflow_cols = st.columns(4)

with workflow_cols[0]:
    st.markdown("### 1️⃣ Collect")
    st.caption("Bright Data collects structured data.")

with workflow_cols[1]:
    st.markdown("### 2️⃣ Detect")
    st.caption("ScrapeShield checks the output schema.")

with workflow_cols[2]:
    st.markdown("### 3️⃣ Heal")
    st.caption("Bright Data repairs broken extraction.")

with workflow_cols[3]:
    st.markdown("### 4️⃣ Recover")
    st.caption("Validated data continues downstream.")


# ---------------------------------------------------------
# URL
# ---------------------------------------------------------

url = st.text_input(
    "Public page URL",
    value=(
        "https://ecommerce-shop-brd.vercel.app/"
        "product/echo-portable-speaker"
    ),
)


# ---------------------------------------------------------
# ACTION BUTTONS
# ---------------------------------------------------------

st.divider()

run_col, break_col = st.columns(2)


with run_col:

    if st.button(
        "▶ Run Bright Data Collector",
        use_container_width=True,
    ):

        if not real_mode:
            st.warning(
                "Demo mode is active. Add "
                "BRIGHT_DATA_API_TOKEN and "
                "BRIGHT_DATA_COLLECTOR_ID to run the "
                "real Bright Data collector."
            )

        else:

            try:
                from brightdata import BrightDataClient

                with st.spinner(
                    "Running Bright Data collector..."
                ):

                    rows, snapshot_id = (
                        BrightDataClient().collect(
                            [{"url": url}]
                        )
                    )

                st.session_state.rows = rows
                st.session_state.snapshot = snapshot_id
                st.session_state.stage = "HEALTHY"

                st.success(
                    f"Collector completed. "
                    f"Received {len(rows)} rows."
                )

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Collector failed: {exc}"
                )


with break_col:

    if st.button(
        "🧪 Simulate Website Redesign",
        use_container_width=True,
    ):

        st.session_state.rows = broken_rows
        st.session_state.stage = "BROKEN"
        st.session_state.last_heal_result = None

        st.rerun()


# ---------------------------------------------------------
# HEALTH RESULT
# ---------------------------------------------------------

st.divider()

if health.healthy:

    st.success(
        f"✅ {health.message}"
    )

else:

    st.error(
        f"🚨 {health.message}"
    )


# ---------------------------------------------------------
# FAILURE DETAILS
# ---------------------------------------------------------

if not health.healthy:

    st.subheader("🔎 Failure Detection")

    st.write(
        "ScrapeShield detected that the expected "
        "output schema is no longer being satisfied."
    )

    st.write(
        "Missing fields:"
    )

    for field in health.missing_fields:
        st.warning(field)


# ---------------------------------------------------------
# SELF-HEAL PROMPT
# ---------------------------------------------------------

prompt = (
    "The latest collection is missing: "
    f"{', '.join(health.missing_fields) if health.missing_fields else 'none'}. "
    "Repair the extraction while preserving the "
    "existing output schema. Prefer stable semantic "
    "selectors and data-test attributes where available. "
    "Validate the repaired extraction against the "
    "expected fields before considering the repair successful."
)


if not health.healthy:

    st.subheader("🤖 Self-Healing Instruction")

    st.code(
        prompt,
        language="text",
    )


# ---------------------------------------------------------
# SELF HEAL BUTTONS
# ---------------------------------------------------------

heal_col, demo_col = st.columns(2)


with heal_col:

    if st.button(
        "🤖 Self-Heal in Bright Data",
        use_container_width=True,
        disabled=health.healthy,
    ):

        if not real_mode:

            st.warning(
                "Real Bright Data Self-Healing requires "
                "your Bright Data API token and collector ID."
            )

        else:

            try:

                from brightdata import BrightDataClient

                with st.spinner(
                    "Starting Bright Data Self-Healing..."
                ):

                    result = (
                        BrightDataClient().self_heal(
                            prompt
                        )
                    )

                st.session_state.last_heal_result = result
                st.session_state.stage = "HEALING"

                st.success(
                    "Bright Data Self-Healing request started."
                )

                st.json(result)

            except Exception as exc:

                st.error(
                    f"Self-Healing failed: {exc}"
                )


with demo_col:

    if st.button(
        "⚡ Apply Demo Repair",
        use_container_width=True,
        disabled=health.healthy,
    ):

        repaired = demo_repair(
            st.session_state.rows,
            health.missing_fields,
        )

        st.session_state.rows = repaired
        st.session_state.stage = "RECOVERED"

        st.success(
            "🎉 Extraction repaired successfully!"
        )

        st.rerun()


# ---------------------------------------------------------
# RECOVERY STATUS
# ---------------------------------------------------------

if health.healthy:

    st.info(
        "🟢 Downstream systems receive complete structured data."
    )


# ---------------------------------------------------------
# STRUCTURED OUTPUT
# ---------------------------------------------------------

st.divider()

st.subheader("📊 Structured Output")


clean_rows = []

for row in st.session_state.rows:

    clean_row = {
        key: value
        for key, value in row.items()
        if not key.startswith("_")
    }

    clean_rows.append(clean_row)


st.dataframe(
    clean_rows,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# SNAPSHOT INFORMATION
# ---------------------------------------------------------

if st.session_state.snapshot:

    st.caption(
        f"Bright Data collection ID: "
        f"{st.session_state.snapshot}"
    )


# ---------------------------------------------------------
# DEMO INSTRUCTIONS
# ---------------------------------------------------------

st.divider()

with st.expander("🎬 Hackathon Demo Flow"):

    st.markdown(
        """
**Recommended demo:**

1. Start with the dashboard in HEALTHY state.
2. Show the structured product data.
3. Click **Simulate Website Redesign**.
4. Show that the `price` field disappeared.
5. Explain that ScrapeShield detected the schema failure.
6. Show the generated self-healing instruction.
7. Click **Apply Demo Repair** for the guaranteed demo recovery.
8. Show the recovered price data.
9. If Bright Data credentials are configured, also demonstrate
   the real **Self-Heal in Bright Data** flow.
"""
    )


st.caption(
    "ScrapeShield AI • Built for Into the Scrape-Verse 2026"
)
