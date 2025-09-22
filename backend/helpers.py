import os
import requests
from urllib.parse import urlencode

OPENMETEO_BASE = os.getenv("OPENMETEO_BASE", "https://api.open-meteo.com/v1")

def fetch_weather(lat, lon, days=7):
    """
    Fetch forecast & recent historical (archive/historical-forecast) from Open-Meteo.
    Returns a compact dict of daily/hourly variables.
    Docs: https://open-meteo.com/en/docs
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,relativehumidity_2m,soil_moisture_0_1cm",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
        "forecast_days": days
    }
    url = f"{OPENMETEO_BASE}/forecast?{urlencode(params)}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_historical_weather(lat, lon, start_date, end_date):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "timezone": "Asia/Kolkata"
    }
    url = f"{OPENMETEO_BASE}/archive?{urlencode(params)}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_sachet_alerts(lat, lon, radius_km=50):
    """
    SACHET provides public alerts. The portal does not have a single documented JSON API for all consumers
    in one place — but the dashboard and CAP feeds are usable. Here we query the SACHET dashboard tile
    via its public endpoints if available or fall back to scraping their site.
    NOTE: Production deployments should implement CAP feed parsing and subscribe to push alerts (or NDMA APIs).
    """
    base = "https://sachet.ndma.gov.in/api"  # placeholder: the real CAP feed or NDMA API should be used
    try:
        r = requests.get(f"{base}/alerts?lat={lat}&lon={lon}&radius={radius_km}", timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # Fallback: return empty
    return {"alerts": []}

def fetch_soil_health_card_by_farmer_id(farmer_id):
    """
    Placeholder hook for Soil Health Card queries. The Soil Health Card portal (soilhealth.dac.gov.in)
    and data.gov.in provide datasets. Typically you search by Aadhaar/ID or district.
    For an MVP we will rely on user-provided local SHC ID or district data from data.gov.in.
    """
    # In production, integrate with central Soil Health Card API / state portal.
    return {"soil_health_card": None}

def fetch_mandi_prices(commodity, district):
    """
    Placeholder: try to get mandi prices from data.gov.in or state mandi APIs.
    For illustration, return a sample structure. Replace by Upstox/mandi API integration.
    """
    # TODO: integrate with state mandi portal or Upstox if agri spot data available
    return {
        "commodity": commodity,
        "district": district,
        "latest_price": None,
        "prices": []
    }