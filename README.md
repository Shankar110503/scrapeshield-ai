# ScrapeShield AI — Fixed Build

## Streamlit Cloud main file

Use:

`app/dashboard.py`

## Important fix

The previous dashboard used relative imports such as:

`from .brightdata import BrightDataClient`

When Streamlit launches `app/dashboard.py` as the main script, that can produce an ImportError.

This version uses:

`from app.brightdata import BrightDataClient`

and adds the repository root to `sys.path`.

## Bright Data polling fix

A response like:

`{"status":"collecting","message":"Job is not finished"}`

is treated as an asynchronous "still running" state. The app waits and polls again instead of treating it as a fatal dataset error.

## Secrets

In Streamlit Cloud → Manage app → Settings → Secrets:

```toml
BRIGHT_DATA_API_TOKEN = "YOUR_TOKEN"
BRIGHT_DATA_COLLECTOR_ID = "YOUR_COLLECTOR_ID"
```

Never commit the token to GitHub.
