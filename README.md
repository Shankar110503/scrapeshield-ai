# ScrapeShield AI

Self-healing web scraper reliability layer for the Into the Scrape-Verse hackathon.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/dashboard.py
```

## Streamlit Cloud secrets

Add these two secrets:

```toml
BRIGHT_DATA_API_TOKEN = "YOUR_TOKEN"
BRIGHT_DATA_COLLECTOR_ID = "YOUR_COLLECTOR_ID"
```

Do not commit the real token to GitHub.

## Important fix

Bright Data collection is asynchronous. A response such as:

```text
{"status":"collecting","message":"Job is not finished"}
```

is treated as a normal polling state. The client waits and checks again instead of displaying a fatal collector error.

The dashboard also has a DEMO mode so the complete Collect → Detect → Heal → Recover flow can be demonstrated without credentials.
