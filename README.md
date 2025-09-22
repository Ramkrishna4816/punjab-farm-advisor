# Punjab Farm Advisor (React + Flask + Gemini)

## Overview
This project is an MVP scaffold for a Punjab-focused farm advisory chatbot:
- Uses Open-Meteo for weather & historical forecast. (no key required)
- Uses India OGD (data.gov.in) & state Punjab datasets for soil / Soil Health Card data.
- Uses NDMA / SACHET for disaster alert ingestion.
- Placeholder integration points for Upstox / mandi market data and fertilizer DBT references.
- Uses Google Gemini (free tier) as the reasoning engine; the backend compiles a compact *fact bundle* that Gemini consults for each request.

APIs verified:
- Open-Meteo docs: https://open-meteo.com/en/docs. :contentReference[oaicite:8]{index=8}
- Punjab / data.gov.in soil datasets. :contentReference[oaicite:9]{index=9}
- SACHET / NDMA alerts. :contentReference[oaicite:10]{index=10}
- Upstox developer docs (for market data). :contentReference[oaicite:11]{index=11}
- Department of Fertilizers DBT pages. :contentReference[oaicite:12]{index=12}
- Gemini API docs (Google AI). :contentReference[oaicite:13]{index=13}

## Quickstart (local)
1. Backend
   - cd backend
   - Copy .env.example to .env and set GEMINI_API_KEY.
   - python3 -m venv venv && source venv/bin/activate
   - pip install -r requirements.txt
   - python app.py (runs on port 5000)

2. Frontend
   - cd frontend
   - npm install
   - npm run dev (Vite serves at :5173; proxies /api to backend)

## Production notes & security
- *Gemini Key*: use short-lived service account tokens when possible, and never embed keys into the client. The backend uses the key.
- *Rate limits*: Gemini free tier or promo may impose prompt limits; batch prompts sensibly and provide local logic to avoid hitting daily caps. Monitor and optionally add queuing or paid tier.
- *Data normalization*: For field-level compliance with Indian regulation and DBT advice, create a local canonical dataset of fertilizer subsidy rules (DBT) updated periodically from fert.nic.in and state portals; do not rely purely on model memory.
- *Audit & traceability*: Log which facts were used to produce each recommendation (the app instructs Gemini to mention which bundle keys it used, but you must also persist the bundled facts + model output for audit).

## Extending market & mandi integration
- Use state mandi portals or combine with Upstox/commodity APIs. Upstox has developer docs for orders/market streaming; for real mandi prices, prefer official state agri market portals or data.gov.in mandi datasets. :contentReference[oaicite:14]{index=14}

## Regulatory compliance
- For pesticide/fertilizer licensing, link and surface authoritative pages from india.gov.in and state departments. Do not provide legal advice — only direct users to the relevant forms & official portals. :contentReference[oaicite:15]{index=15}
