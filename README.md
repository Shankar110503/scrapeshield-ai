# 🛡️ ScrapeShield AI

> **Self-healing web scraping engine powered by Bright Data Scraper Studio & CLI.**

ScrapeShield AI automatically detects when target website layouts change, catches missing data fields, and triggers automated self-healing via `bdata scraper heal` — preventing downstream data breakage.

---

## 🚀 Key Features

* **Terminal-First Workflow**: Seamless execution via Bright Data CLI inside coding agents.
* **Autonomous Self-Healing**: Automatically repairs broken selectors upon detecting empty or `null` extraction fields.
* **Live Health Dashboard**: Real-time status monitoring built with Streamlit.
* **Production API Trigger**: Collector ID (`c_*`) ready for POST requests and scheduler integration.

---

## 🛠️ Quick Start

### 1. Requirements
Ensure Node.js and Python 3.10+ are installed.

```bash
pip install -r requirements.txt
npx -p @brightdata/cli bdata login
