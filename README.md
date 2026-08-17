# ScrapeShield AI
Self-healing web scraper monitor for Into the Scrape-Verse 2026.

Flow: Bright Data collector → schema health check → failure detection → Bright Data Self-Healing → re-run → validation.

## Run
pip install -r requirements.txt
streamlit run app/dashboard.py

Copy `.env.example` to `.env` and add your Bright Data API token and `c_...` collector ID. Never commit `.env`.
