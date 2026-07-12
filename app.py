from flask import Flask, render_template, request

from weather_app import get_current_weather, get_forecast_weather, get_weather_description

app = Flask(__name__)
app.static_folder = "assets"


@app.route("/", methods=["GET", "POST"])
def index():
    city = request.form.get("city") or request.args.get("city") or "Istanbul"

    try:
        weather = get_current_weather(city)
        forecast_data = get_forecast_weather(city, days=5)
        forecast = forecast_data.get("forecast", [])
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
