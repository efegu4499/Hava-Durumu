import os
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


def build_daily_summary(weather, forecast, hourly):
    if not weather:
        return None

    parts = []
    temp = weather.get("temperature")
    desc = weather.get("description")
    if temp is not None and desc:
        parts.append(f"Şu an {temp}°C ve {desc.lower()}.")

    if forecast:
        today = forecast[0]
        max_temp = today.get("max_temp")
        min_temp = today.get("min_temp")
        if max_temp is not None and min_temp is not None:
            parts.append(f"Bugün {max_temp}° / {min_temp}° aralığında.")

        rain_mm = today.get("precipitation_sum_mm")
        snow_cm = today.get("snowfall_sum_cm")
        if rain_mm is not None and rain_mm > 0:
            parts.append(f"Günlük yağış beklentisi {rain_mm} mm.")
        if snow_cm is not None and snow_cm > 0:
            parts.append(f"Günlük kar beklentisi {snow_cm} cm.")

    if hourly:
        next_hours = hourly[:6]
        peak_rain = max((item.get("precipitation_mm") or 0) for item in next_hours) if next_hours else 0
        peak_snow = max((item.get("snowfall_cm") or 0) for item in next_hours) if next_hours else 0
        if peak_rain > 0:
            parts.append(f"Önümüzdeki saatlerde en yüksek saatlik yağış {peak_rain} mm.")
        if peak_snow > 0:
            parts.append(f"Önümüzdeki saatlerde en yüksek saatlik kar {peak_snow} cm.")

    wind_speed = weather.get("wind_speed")
    wind_direction = weather.get("wind_direction_text")
    if wind_speed is not None:
        if wind_direction:
            parts.append(f"Rüzgar {wind_speed} km/s, {wind_direction.lower()} yönünde.")
        else:
            parts.append(f"Rüzgar hızı {wind_speed} km/s.")

    if not parts:
        return "Bugünün özeti için veri hazırlanıyor."
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

    try:
        weather = get_current_weather(city)
        forecast_data = get_forecast_weather(city, days=5)
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
        weather["description"] = get_weather_description(weather["weather_code"])
        hourly = get_hourly_weather(city, hours=24)
        day_summary = build_daily_summary(weather, forecast, hourly)
    except Exception as exc:
        weather = None
        forecast = []
        hourly = []
        day_summary = None
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
        error=error,
    )


def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    start_server()
