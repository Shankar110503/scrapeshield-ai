# 🛡️ ScrapeShield AI — Autonomous Self-Healing Web Scraper

> Built for **Into the Scrape-Verse Hackathon** by Bright Data & WeMakeDevs.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://scrapshield-ai-dashboard-bsy6h7.streamlit.app)

ScrapeShield AI is an intelligent scraping pipeline that monitors target websites, automatically detects layout/selector breakage, and repairs itself in real-time using Bright Data's `bdata scraper heal` engine — ensuring zero downtime for downstream data consumers.

---

## 🌟 Key Features

- **Autonomous Self-Healing**: Automatically detects `null` or missing data fields and triggers `bdata scraper heal` with plain-language prompts.
- **Terminal-First Integration**: Designed around the `@brightdata/cli` workflow for Claude Code, Cursor, and Codex.
- **Interactive Live Dashboard**: Built with Streamlit, providing real-time metrics, execution logs, and output JSON visualization.
- **Instant Production API**: Powered by Bright Data Collector endpoints (`c_*`).

---

## 📌 Hackathon Project Proofs

- **Primary Collector ID**: `c_msy918t12pt7dsk0kp`
- **Target URL**: `https://ecommerce-shop-brd.vercel.app/product/echo-portable-speaker`
- **Live Interactive Dashboard**: [https://scrapshield-ai-dashboard-bsy6h7.streamlit.app](https://scrapshield-ai-dashboard-bsy6h7.streamlit.app)

---

## ⚙️ How It Works

1. **Extraction Stage**: Runs `bdata scraper run <collector_id> <url> --pretty` to pull structured JSON.
2. **Detection Stage**: The `AutoHealer` engine validates extracted fields against expected keys.
3. **Healing Stage**: If fields return empty/null due to DOM changes, `bdata scraper heal` rewrites selectors on the fly.
4. **Data Flow Continues**: Clean, restored JSON is passed downstream without human intervention.

---

## 🚀 Quick Setup & Local Running

```bash
# Clone the repository
git clone [https://github.com/Shankar110503/scrapeshield-ai.git](https://github.com/Shankar110503/scrapeshield-ai.git)
cd scrapeshield-ai

# Install Python dependencies
pip install -r requirements.txt

# Login to Bright Data CLI
npx -p @brightdata/cli bdata login

# Launch Dashboard
streamlit run app/dashboard.py
