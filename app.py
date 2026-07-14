import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory

from weather_app import (
    _normalize_text,
    get_current_weather,
    get_forecast_weather,
    get_hourly_weather,
    get_weather_description,
    suggest_locations,
)

app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(__file__), "assets")


SKI_RESORTS = [
    {
        "name": "Uludag",
        "region": "Bursa",
        "latitude": 40.0928,
        "longitude": 29.2216,
        "report_url": "https://www.snow-forecast.com/resorts/Uludag",
    },
    {
        "name": "Erciyes",
        "region": "Kayseri",
        "latitude": 38.5311,
        "longitude": 35.4487,
        "report_url": "https://www.snow-forecast.com/resorts/Erciyes",
    },
    {
        "name": "Palandoken",
        "region": "Erzurum",
        "latitude": 39.8555,
        "longitude": 41.2743,
        "report_url": "https://www.snow-forecast.com/resorts/Palandoken",
    },
    {
        "name": "Kartalkaya",
        "region": "Bolu",
        "latitude": 40.5966,
        "longitude": 31.7298,
        "report_url": "https://www.snow-forecast.com/resorts/Kartalkaya",
    },
    {
        "name": "Sarikamis",
        "region": "Kars",
        "latitude": 40.3521,
        "longitude": 42.5984,
        "report_url": "https://www.snow-forecast.com/resorts/Sarikamis",
    },
]


def get_background_theme(weather_code):
    if weather_code in (0, 1, 2):
        return "sunny"
    if weather_code in (3, 45, 48):
        return "cloudy"
    if weather_code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    if weather_code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99):
        return "rainy"
    return "cloudy"


def get_ui_texts(lang):
    if lang == "en":
        return {
            "title": "Gokyra Weather",
            "city_placeholder": "Enter district or city name",
            "search": "Search",
            "add_favorite": "Add Favorite",
            "favorites_title": "My Favorite Cities",
            "clear_all": "Clear All",
            "summary_title": "Daily Summary",
            "temperature": "Temperature",
            "feels_like": "Feels Like",
            "humidity": "Humidity",
            "wind": "Wind",
            "status": "Status",
            "hourly_title": "Hourly Forecast (24 Hours)",
            "daily_title": "5-Day Forecast",
            "precip": "Precip",
            "snow": "Snow",
            "no_favorites": "No favorite cities yet.",
            "searching": "Searching...",
            "ski_tab": "Ski Snow",
        }

    return {
        "title": "Gokyra Weather",
        "city_placeholder": "Ilce veya il adi girin",
        "search": "Sorgula",
        "add_favorite": "Favoriye Ekle",
        "favorites_title": "Favori Sehirlerim",
        "clear_all": "Tumunu Temizle",
        "summary_title": "Gunun Ozeti",
        "temperature": "Sicaklik",
        "feels_like": "Hissedilen",
        "humidity": "Nem",
        "wind": "Ruzgar",
        "status": "Durum",
        "hourly_title": "Saatlik Tahmin (24 Saat)",
        "daily_title": "5 Gunluk Tahmin",
        "precip": "Yagis",
        "snow": "Kar",
        "no_favorites": "Henuz favori sehir yok.",
        "searching": "Araniyor...",
        "ski_tab": "Kayak Merkezleri Kar Birikimi",
    }


def get_ski_texts(lang):
    if lang == "en":
        return {
            "title": "Ski Resort Snow Depth",
            "subtitle": "Current modeled snow depth and live report links for major resorts.",
            "depth": "Current Snow Depth",
            "updated": "Updated",
            "open_report": "Open Snow Report",
            "back": "Back To Weather",
            "unavailable": "Data unavailable",
        }

    return {
        "title": "Kayak Merkezleri Kar Birikimi",
        "subtitle": "Buyuk merkezler icin anlik model kar birikimi ve canli rapor baglantisi.",
        "depth": "Guncel Kar Birikimi",
        "updated": "Guncellendi",
        "open_report": "Kar Raporunu Ac",
        "back": "Hava Durumuna Don",
        "unavailable": "Veri alinamadi",
    }


def _fetch_open_meteo_current(lat, lon):
    query = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": "snow_depth,temperature_2m",
            "timezone": "auto",
            "models": "ecmwf_ifs025",
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{query}"
    request = Request(url, headers={"User-Agent": "weather-app/1.0"})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_ski_resorts_snow_data(lang="tr"):
    items = []
    for resort in SKI_RESORTS:
        snow_depth_cm = None
        updated_at = None
        try:
            data = _fetch_open_meteo_current(resort["latitude"], resort["longitude"])
            current = data.get("current") or {}
            depth_m = current.get("snow_depth")
            if depth_m is not None:
                snow_depth_cm = round(float(depth_m) * 100, 1)
            updated_at = current.get("time")
        except Exception:
            snow_depth_cm = None

        items.append(
            {
                "name": resort["name"],
                "region": resort["region"],
                "snow_depth_cm": snow_depth_cm,
                "updated_at": updated_at,
                "report_url": resort["report_url"],
            }
        )
    return items


def build_daily_summary(weather, forecast, hourly, lang="tr"):
    if not weather:
        return None

    is_en = lang == "en"

    parts = []
    snow_warning_needed = False
    temp = weather.get("temperature")
    felt_temp = weather.get("felt_temperature")
    desc = weather.get("description")
    if temp is not None and desc:
        if felt_temp is not None:
            if is_en:
                parts.append(f"Now {temp}°C, feels like {felt_temp}°C and {desc.lower()}.")
            else:
                parts.append(f"Su an {temp}°C, hissedilen {felt_temp}°C ve {desc.lower()}.")
        else:
            if is_en:
                parts.append(f"Now {temp}°C and {desc.lower()}.")
            else:
                parts.append(f"Su an {temp}°C ve {desc.lower()}.")

    current_temp = weather.get("temperature")
    today_min_temp = None

    if forecast:
        today = forecast[0]
        max_temp = today.get("max_temp")
        min_temp = today.get("min_temp")
        today_min_temp = min_temp
        if max_temp is not None and min_temp is not None:
            if is_en:
                parts.append(f"Today between {max_temp}° / {min_temp}°.")
            else:
                parts.append(f"Bugün {max_temp}° / {min_temp}° aralığında.")

        rain_mm = today.get("precipitation_sum_mm")
        snow_cm = today.get("snowfall_sum_cm")
        if rain_mm is not None:
            if rain_mm > 0:
                if is_en:
                    parts.append(f"Expected daily precipitation: {rain_mm} mm.")
                else:
                    parts.append(f"Günlük yağış beklentisi {rain_mm} mm.")
                if rain_mm > 50:
                    parts.append("Watch for flood risk." if is_en else "Sel ve taşkın ihtimaline dikkat.")
            else:
                parts.append("No precipitation expected today." if is_en else "Bugün yağış beklenmiyor.")
        # Only mention "no snow" when temperatures are realistically close to snow conditions.
        cold_enough_for_snow = (
            (current_temp is not None and current_temp <= 5)
            or (today_min_temp is not None and today_min_temp <= 3)
        )

        if snow_cm is not None:
            if snow_cm > 0:
                if is_en:
                    parts.append(f"Expected daily snowfall: {snow_cm} cm.")
                else:
                    parts.append(f"Günlük kar beklentisi {snow_cm} cm.")
                if snow_cm >= 20:
                    snow_warning_needed = True
            elif cold_enough_for_snow:
                parts.append("No snow expected today." if is_en else "Bugün kar yağışı beklenmiyor.")

    if hourly:
        next_hours = hourly[:6]
        peak_rain = max((item.get("precipitation_mm") or 0) for item in next_hours) if next_hours else 0
        peak_snow = max((item.get("snowfall_cm") or 0) for item in next_hours) if next_hours else 0
        if peak_rain > 0:
            if is_en:
                parts.append(f"Peak hourly precipitation in the next hours: {peak_rain} mm.")
            else:
                parts.append(f"Önümüzdeki saatlerde en yüksek saatlik yağış {peak_rain} mm.")
        else:
            parts.append("No precipitation expected in the next hours." if is_en else "Önümüzdeki saatlerde yağış beklenmiyor.")
        next_hours_min_temp = min((item.get("temperature") for item in next_hours if item.get("temperature") is not None), default=None)
        cold_next_hours = (
            (next_hours_min_temp is not None and next_hours_min_temp <= 3)
            or (current_temp is not None and current_temp <= 5)
        )

        if peak_snow > 0:
            if is_en:
                parts.append(f"Peak hourly snowfall in the next hours: {peak_snow} cm.")
            else:
                parts.append(f"Önümüzdeki saatlerde en yüksek saatlik kar {peak_snow} cm.")
        elif cold_next_hours:
            parts.append("No snow expected in the next hours." if is_en else "Önümüzdeki saatlerde kar beklenmiyor.")

    wind_speed = weather.get("wind_speed")
    wind_direction = weather.get("wind_direction_text")
    if wind_speed is not None:
        if wind_direction:
            if is_en:
                parts.append(f"Wind {wind_speed} km/h from {wind_direction.lower()}.")
            else:
                parts.append(f"Rüzgar {wind_speed} km/s, {wind_direction.lower()} yönünde.")
        else:
            parts.append(f"Wind speed {wind_speed} km/h." if is_en else f"Rüzgar hızı {wind_speed} km/s.")

    if snow_warning_needed:
        parts.append(
            "Roads may close; winter tires and chains are strongly recommended."
            if is_en
            else "Yollar kapanabilir, kar lastiği ve zincir takınız mutlaka."
        )

    if not parts:
        return "Summary is being prepared." if is_en else "Bugünün özeti için veri hazırlanıyor."
    return " ".join(parts)


@app.route("/google7d6f90b41b936c54.html", methods=["GET"])
def google_verification():
    return send_file("google7d6f90b41b936c54.html")


@app.route("/manifest.webmanifest", methods=["GET"])
def manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")


@app.route("/service-worker.js", methods=["GET"])
def service_worker():
    return send_from_directory(app.static_folder, "service-worker.js", mimetype="application/javascript")


@app.route("/api/locations", methods=["GET"])
def locations():
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify([])

    try:
        items = suggest_locations(query, limit=12)
    except Exception:
        items = []

    return jsonify(items)


@app.route("/", methods=["GET", "POST"])
def index():
    city = request.form.get("city") or request.args.get("city") or "Istanbul"
    lang = (request.form.get("lang") or request.args.get("lang") or "tr").strip().lower()
    if lang not in {"tr", "en"}:
        lang = "tr"
    ui_texts = get_ui_texts(lang)

    try:
        weather = get_current_weather(city)
        forecast_data = get_forecast_weather(city, days=5, lang=lang)
        forecast = forecast_data.get("forecast", [])
        city_norm = _normalize_text(weather["city"])
        seen_norms = {city_norm}
        location_parts = [weather["city"]]

        for field in ("admin2", "admin1"):
            val = weather.get(field) or ""
            if val and _normalize_text(val) not in seen_norms:
                seen_norms.add(_normalize_text(val))
                location_parts.append(val)

        if weather.get("country"):
            location_parts.append(weather["country"])

        weather["location_text"] = ", ".join(location_parts)
        weather["description"] = get_weather_description(weather["weather_code"], lang=lang)
        hourly = get_hourly_weather(city, hours=24, lang=lang)
        day_summary = build_daily_summary(weather, forecast, hourly, lang=lang)
        weather_theme = get_background_theme(weather.get("weather_code"))
    except Exception as exc:
        weather = None
        forecast = []
        hourly = []
        day_summary = None
        weather_theme = "cloudy"
        error = str(exc)
    else:
        error = None

    return render_template(
        "index.html",
        city=city,
        weather=weather,
        forecast=forecast,
        hourly=hourly,
        day_summary=day_summary,
        weather_theme=weather_theme,
        lang=lang,
        ui_texts=ui_texts,
        error=error,
    )


@app.route("/kayak-merkezleri", methods=["GET"])
def ski_resorts():
    lang = (request.args.get("lang") or "tr").strip().lower()
    if lang not in {"tr", "en"}:
        lang = "tr"

    return render_template(
        "ski_resorts.html",
        lang=lang,
        ui_texts=get_ui_texts(lang),
        ski_texts=get_ski_texts(lang),
        resorts=get_ski_resorts_snow_data(lang=lang),
    )


def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    start_server()
