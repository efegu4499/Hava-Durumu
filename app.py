import os
from flask import Flask, render_template, request

from weather_app import get_current_weather, get_forecast_weather, get_weather_description

app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(__file__), "assets")


@app.route("/", methods=["GET", "POST"])
def index():
    city = request.form.get("city") or request.args.get("city") or "Istanbul"

    try:
        weather = get_current_weather(city)
        forecast_data = get_forecast_weather(city, days=5)
        forecast = forecast_data.get("forecast", [])
        location_parts = [weather["city"]]
        if weather.get("admin2") and weather["admin2"] != weather["city"]:
            location_parts.append(weather["admin2"])
        if weather.get("admin1") and weather["admin1"] not in location_parts:
            location_parts.append(weather["admin1"])
        if weather.get("country"):
            location_parts.append(weather["country"])
        weather["location_text"] = ", ".join(location_parts)
        weather["description"] = get_weather_description(weather["weather_code"])
    except Exception as exc:
        weather = None
        forecast = []
        error = str(exc)
    else:
        error = None

    return render_template(
        "index.html",
        city=city,
        weather=weather,
        forecast=forecast,
        error=error,
    )


def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    start_server()
