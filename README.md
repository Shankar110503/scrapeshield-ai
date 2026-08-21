# ScrapeShield AI — Fixed v3

This version fixes the Bright Data result endpoint used by the Streamlit app.

## Important fix

The Scraper Studio flow is:

1. `POST /dca/trigger?collector=...&queue_next=1`
2. Receive `collection_id`
3. Poll `GET /dca/dataset?id=<collection_id>` every few seconds
4. Continue when the API says the job is still collecting
5. Use the returned JSON array as structured output

The old version incorrectly called `/dca/get_result?collection_id=...`, which caused:
`Bright Data dataset error 400: Missing response_id parameter`.

## Streamlit

Main file:

`app/dashboard.py`

Secrets:

- `BRIGHT_DATA_API_TOKEN`
- `BRIGHT_DATA_COLLECTOR_ID`
