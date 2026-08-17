# Android step-by-step

1. Download the ZIP and extract it.
2. GitHub → New repository → `scrapeshield-ai`.
3. Upload every extracted file, preserving the `app/` and `prompts/` folders.
4. Do NOT upload `.env` or your API token.
5. Bright Data → create API token.
6. Bright Data Scraper Studio → create a collector for a public product page with output fields `product_name`, `price`, `stock`, `url`.
7. Save the collector to Production and copy its ID beginning with `c_`.
8. Streamlit Community Cloud → connect GitHub → select `scrapeshield-ai` → main file `app/dashboard.py`.
9. Add Secrets:
   `BRIGHT_DATA_API_TOKEN = "YOUR_TOKEN"`
   `BRIGHT_DATA_COLLECTOR_ID = "c_YOUR_ID"`
10. Deploy.
11. Demo: Run collector → Simulate website redesign → show BROKEN → use Bright Data Self-Heal → rerun collector → show recovered schema.

Never commit your API token to GitHub.
