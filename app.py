"""
Weather App – Flask Backend
- All API calls are server-side (no keys exposed to the browser)
- Uses Open-Meteo (free, no API key required)
- Server-side rendering via Jinja2
"""

from flask import Flask, render_template, request
from datetime import datetime
import requests

app = Flask(__name__)

# ============================================================
# CONFIGURATION & MAPPINGS
# ============================================================

WEATHER_CODE_TO_CONDITION = {
    0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing Rime Fog", 51: "Light Drizzle",
    53: "Moderate Drizzle", 55: "Dense Drizzle", 61: "Slight Rain",
    63: "Moderate Rain", 65: "Heavy Rain", 71: "Slight Snow",
    73: "Moderate Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers",
    82: "Violent Rain Showers", 85: "Slight Snow Showers",
    86: "Heavy Snow Showers", 95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail", 99: "Thunderstorm with Heavy Hail",
}

COUNTRY_CODE_MAP = {
    "uk": "GB", "united kingdom": "GB", "britain": "GB",
    "great britain": "GB", "england": "GB", "scotland": "GB", "wales": "GB",
    "usa": "US", "us": "US", "united states": "US", "america": "US",
    "united states of america": "US", "uae": "AE", "united arab emirates": "AE",
    "ghana": "GH", "nigeria": "NG", "south africa": "ZA", "kenya": "KE",
    "egypt": "EG", "germany": "DE", "france": "FR", "spain": "ES",
    "italy": "IT", "portugal": "PT", "netherlands": "NL", "belgium": "BE",
    "switzerland": "CH", "austria": "AT", "poland": "PL", "sweden": "SE",
    "norway": "NO", "denmark": "DK", "finland": "FI", "ireland": "IE",
    "greece": "GR", "china": "CN", "japan": "JP", "india": "IN",
    "australia": "AU", "new zealand": "NZ", "singapore": "SG",
    "malaysia": "MY", "thailand": "TH", "indonesia": "ID",
    "philippines": "PH", "vietnam": "VN", "south korea": "KR", "korea": "KR",
    "canada": "CA", "mexico": "MX", "brazil": "BR", "argentina": "AR",
    "chile": "CL", "colombia": "CO", "peru": "PE", "saudi arabia": "SA",
    "israel": "IL", "turkey": "TR", "iran": "IR", "iraq": "IQ", "russia": "RU",
}

WEATHER_BACKGROUNDS = {
    "sunny":  "https://images.unsplash.com/photo-1601297183305-6df142704ea2?w=1920&q=80",
    "cloudy": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=1920&q=80",
    "rainy":  "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=1920&q=80",
    "snowy":  "https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=1920&q=80",
    "foggy":  "https://images.unsplash.com/photo-1485236715568-ddc5ee6ca227?w=1920&q=80",
    "stormy": "https://images.unsplash.com/photo-1605727216801-e27ce1d0cc28?w=1920&q=80",
}
DEFAULT_BACKGROUND = "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1920&q=80"

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL  = "https://api.open-meteo.com/v1/forecast"

# ============================================================
# HELPERS
# ============================================================

def parse_search_input(raw: str) -> tuple[str, str | None]:
    """Return (city, country_code | None) from raw search string."""
    sanitized = " ".join(raw.strip().split())

    if "," in sanitized:
        city, _, rest = sanitized.partition(",")
        country_input = rest.strip().lower()
        country_code = (
            COUNTRY_CODE_MAP.get(country_input)
            or (country_input.upper() if len(country_input) == 2 else None)
        )
        return city.strip(), country_code

    words = sanitized.split()
    if len(words) >= 2:
        last      = words[-1].lower()
        last_two  = " ".join(words[-2:]).lower() if len(words) >= 3 else None

        if last_two and COUNTRY_CODE_MAP.get(last_two):
            return " ".join(words[:-2]), COUNTRY_CODE_MAP[last_two]
        if COUNTRY_CODE_MAP.get(last):
            return " ".join(words[:-1]), COUNTRY_CODE_MAP[last]
        if len(last) == 2 and last.isalpha():
            return " ".join(words[:-1]), last.upper()

    return sanitized, None


def geocode(city: str) -> list[dict]:
    resp = requests.get(
        GEOCODE_URL,
        params={"name": city, "count": 10, "language": "en", "format": "json"},
        timeout=8,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def best_match(results: list[dict], country_code: str | None) -> dict | None:
    if not results:
        return None
    if country_code:
        return next(
            (r for r in results if r.get("country_code", "").upper() == country_code.upper()),
            None,
        )
    return results[0]


def weather_background(code: int) -> str:
    if code in (0, 1):                                    return WEATHER_BACKGROUNDS["sunny"]
    if code in (2, 3):                                    return WEATHER_BACKGROUNDS["cloudy"]
    if code in (45, 48):                                  return WEATHER_BACKGROUNDS["foggy"]
    if (51 <= code <= 67) or (80 <= code <= 82):          return WEATHER_BACKGROUNDS["rainy"]
    if (71 <= code <= 77) or (85 <= code <= 86):          return WEATHER_BACKGROUNDS["snowy"]
    if code in (95, 96, 99):                              return WEATHER_BACKGROUNDS["stormy"]
    return DEFAULT_BACKGROUND


def icon_type(code: int) -> str:
    if code in (0, 1):                                    return "sunny"
    if code == 2:                                         return "partly-cloudy"
    if code in (3, 45, 48):                               return "cloudy"
    if (51 <= code <= 67) or (80 <= code <= 82):          return "rain"
    if (71 <= code <= 77) or (85 <= code <= 86):          return "snow"
    if code >= 95:                                        return "storm"
    return "sunny"


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html", state="initial", background=DEFAULT_BACKGROUND)


@app.route("/weather")
def weather():
    query = request.args.get("q", "").strip()

    if not query:
        return render_template("index.html", state="initial", background=DEFAULT_BACKGROUND)

    def err(msg):
        return render_template(
            "index.html", state="error", error=msg,
            background=DEFAULT_BACKGROUND, query=query,
        )

    try:
        city, country_code = parse_search_input(query)

        if not city:
            return err("Please enter a city name.")

        # Geocode with typo-tolerance fallback
        results = geocode(city)
        if not results and len(city) > 3:
            results = geocode(city[:-1])

        location = best_match(results, country_code)

        if not location:
            if country_code and results:
                countries = ", ".join({r.get("country", "") for r in results})
                return err(f'"{city}" was found in: {countries}. No match in your specified country.')
            return err("Location not found. Please check the spelling and try again.")

        lat, lon = location["latitude"], location["longitude"]
        location_display = f"{location['name']}, {location['country']}"

        # Fetch weather
        resp = requests.get(
            WEATHER_URL,
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily":   "weather_code,temperature_2m_max",
                "hourly":  "uv_index",
                "timezone": "auto",
                "forecast_days": 5,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        current_hour = datetime.now().hour
        uv_val       = round(data["hourly"]["uv_index"][current_hour] or 0)
        code         = data["current"]["weather_code"]

        forecast = [
            {
                "day":      datetime.strptime(date_str, "%Y-%m-%d").strftime("%a"),
                "high":     round(data["daily"]["temperature_2m_max"][i + 1]),
                "icon":     icon_type(data["daily"]["weather_code"][i + 1]),
            }
            for i, date_str in enumerate(data["daily"]["time"][1:5])
        ]

        return render_template(
            "index.html",
            state       = "weather",
            query       = query,
            location    = location_display,
            temperature = round(data["current"]["temperature_2m"]),
            condition   = WEATHER_CODE_TO_CONDITION.get(code, "Unknown"),
            humidity    = data["current"]["relative_humidity_2m"],
            wind_speed  = round(data["current"]["wind_speed_10m"]),
            uv_index    = uv_val,
            feels_like  = round(data["current"]["apparent_temperature"]),
            forecast    = forecast,
            icon        = icon_type(code),
            background  = weather_background(code),
        )

    except requests.RequestException:
        return err("Could not reach the weather service. Please try again.")
    except Exception as exc:
        return err(str(exc) or "An unexpected error occurred.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)