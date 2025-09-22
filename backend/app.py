import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from helpers import fetch_weather, fetch_historical_weather, fetch_sachet_alerts, fetch_soil_health_card_by_farmer_id, fetch_mandi_prices

load_dotenv()
app = Flask(_name_)
CORS(app)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://api.generativeai.googleapis.com/v1beta2/models"  # base; we'll use model-specific endpoint in call
GEMINI_MODEL = "gemini-1.5-mini"  # pick a compact model suitable for free tier; change if you have a different one

if not GEMINI_KEY:
    app.logger.warning("GEMINI_API_KEY not set. Gemini calls will fail until you set it in .env")

def build_fact_bundle(lat, lon, farmer_inputs):
    """
    Fetches & compiles weather, soil, alerts, market and subsidy facts into a compact JSON bundle
    that will be passed to Gemini as 'system' context with each user request.
    """
    try:
        weather = fetch_weather(lat, lon, days=7)
    except Exception as e:
        weather = {"error": str(e)}
    try:
        # example: fetch 30 days historical
        # (In production: determine relevant historical window dynamically)
        historical = fetch_historical_weather(lat, lon, start_date=farmer_inputs.get("hist_start","2024-01-01"), end_date=farmer_inputs.get("hist_end","2024-12-31"))
    except Exception:
        historical = {}
    alerts = fetch_sachet_alerts(lat, lon)
    soilhc = fetch_soil_health_card_by_farmer_id(farmer_inputs.get("soil_health_card_id"))
    mandi = fetch_mandi_prices(farmer_inputs.get("commodity", "wheat"), farmer_inputs.get("district"))

    # Fertilizer/subsidy snippet: produce link + short rules (should be normalized offline via scraper or dataset)
    fertilizer_info = {
        "dbt": "Check Department of Fertilizers DBT pages for current subsidy and eligibility rules.",
        "source": "https://fert.nic.in"
    }

    bundle = {
        "location": {"lat": lat, "lon": lon},
        "weather": {
            "forecast": weather.get("daily", {}),
            "hourly": weather.get("hourly", {})
        },
        "historical_weather": historical.get("hourly", {}),
        "alerts": alerts.get("alerts", []) if isinstance(alerts, dict) else [],
        "soil_health_card": soilhc,
        "market": mandi,
        "fertilizer": fertilizer_info,
        "farmer_inputs": farmer_inputs
    }
    # Keep bundle compact: remove huge raw arrays if needed (or summarize)
    return bundle

def call_gemini_system_prompt(fact_bundle, lang="en"):
    """
    Construct a system-level instruction describing the fact bundle and app goals.
    We'll keep it concise and instruct Gemini to answer in both English and Hindi, produce actionable
    recommendations, and cite which facts were used (by key names).
    """
    system_prompt = {
        "role": "system",
        "content": (
            "You are an agricultural advisor for Punjab farmers. "
            "You receive a compact JSON 'fact bundle' that contains weather, soil info, disaster alerts, "
            "local market snapshot, and fertilizer/subsidy notes. "
            "For every farmer request, produce region-specific, implementable advice covering: "
            "1) crop choice, 2) sowing schedule, 3) irrigation & fertilizer plan, 4) pest control, "
            "5) sell timing and market guidance, 6) subsidy suggestions and 7) disaster preparedness / alerts. "
            "Answer bilingually: produce an English section and a Hindi section. "
            "When you use facts from the bundle, explicitly label which fields were used (e.g., weather.forecast, soil_health_card, alerts). "
            "Keep recommendations short, numbered, and actionable. Use local units (kg/ha, mm of water, dates in DD-MMM-YYYY). "
            "If data is missing, say what input is needed (no more than 2 extra items)."
        )
    }
    # include the fact bundle as a context message (JSON string) — but keep size manageable
    bundle_message = {"role": "system", "content": "Fact bundle (json):\n" + json.dumps(fact_bundle, default=str)}
    return [system_prompt, bundle_message]

def call_gemini_api(messages):
    """
    Basic REST call to Gemini text generation endpoint.
    See Google Gemini API docs for up-to-date endpoint & auth: use your API key as Bearer or key param.
    Docs: https://ai.google.dev/gemini-api/docs
    """
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    # Example endpoint path for text chat completions (subject to Google API changes).
    # This is a minimal example for demo; adapt to the official current API surface.
    endpoint = f"https://generativeai.googleapis.com/v1beta2/models/{GEMINI_MODEL}:generateText"
    headers = {
        "Authorization": f"Bearer {GEMINI_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": {
            "messages": messages
        },
        "maxOutputTokens": 800
    }
    r = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

@app.route("/api/fact-bundle", methods=["POST"])
def fact_bundle():
    """
    Accepts JSON with { lat, lon, farmer_inputs }
    Returns a compact fact bundle.
    """
    payload = request.json or {}
    lat = payload.get("lat")
    lon = payload.get("lon")
    farmer_inputs = payload.get("farmer_inputs", {})
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    bundle = build_fact_bundle(lat, lon, farmer_inputs)
    return jsonify(bundle)

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Accepts { lat, lon, farmer_inputs, user_message, lang }.
    Produces Gemini response (bilingual) using fact bundle as context.
    """
    data = request.json or {}
    lat = data.get("lat")
    lon = data.get("lon")
    user_message = data.get("user_message", "")
    farmer_inputs = data.get("farmer_inputs", {})
    lang = data.get("lang", "en")  # 'en' or 'hi' or 'both' (we instruct Gemini to always produce both)
    if not (lat and lon):
        return jsonify({"error": "lat and lon required"}), 400

    bundle = build_fact_bundle(lat, lon, farmer_inputs)
    system_messages = call_gemini_system_prompt(bundle, lang=lang)
    # append user's message
    system_messages.append({"role":"user","content": user_message})

    try:
        resp = call_gemini_api(system_messages)
        # Normalize Gemini response to our format
        return jsonify({"gemini_raw": resp})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if _name_ == "_main_":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)