import os
import time
from urllib.parse import urlencode
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory

from weather_app import (
    _get_json,
    _normalize_text,
    get_current_weather,
    get_weather_description,
    get_weather_bundle,
    suggest_locations,
)

app = Flask(__name__)
app.static_folder = os.path.join(os.path.dirname(__file__), "assets")

_LOCATIONS_CACHE = {}
_LOCATIONS_CACHE_TTL = 300
_PROVINCE_WEATHER_CACHE = {}
_PROVINCE_WEATHER_CACHE_TTL = 180
_SKI_CACHE = {"ts": 0.0, "items": []}
_SKI_CACHE_TTL = 600


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
    {
        "name": "Zermatt",
        "region": "Switzerland",
        "latitude": 46.0207,
        "longitude": 7.7491,
        "report_url": "https://www.snow-forecast.com/resorts/Zermatt",
    },
    {
        "name": "Chamonix",
        "region": "France",
        "latitude": 45.9237,
        "longitude": 6.8694,
        "report_url": "https://www.snow-forecast.com/resorts/Chamonix",
    },
    {
        "name": "St. Anton",
        "region": "Austria",
        "latitude": 47.1275,
        "longitude": 10.2641,
        "report_url": "https://www.snow-forecast.com/resorts/St-Anton",
    },
    {
        "name": "Courchevel",
        "region": "France",
        "latitude": 45.4154,
        "longitude": 6.6341,
        "report_url": "https://www.snow-forecast.com/resorts/Courchevel",
    },
    {
        "name": "Cortina d'Ampezzo",
        "region": "Italy",
        "latitude": 46.5405,
        "longitude": 12.1357,
        "report_url": "https://www.snow-forecast.com/resorts/Cortina-d-Ampezzo",
    },
]

TURKEY_PROVINCES = [
    {"name": "Adana", "lat": 37.0000, "lon": 35.3213},
    {"name": "Adiyaman", "lat": 37.7648, "lon": 38.2786},
    {"name": "Afyonkarahisar", "lat": 38.7569, "lon": 30.5387},
    {"name": "Agri", "lat": 39.7191, "lon": 43.0503},
    {"name": "Amasya", "lat": 40.6499, "lon": 35.8353},
    {"name": "Ankara", "lat": 39.9208, "lon": 32.8541},
    {"name": "Antalya", "lat": 36.8841, "lon": 30.7056},
    {"name": "Artvin", "lat": 41.1828, "lon": 41.8183},
    {"name": "Aydin", "lat": 37.8444, "lon": 27.8458},
    {"name": "Balikesir", "lat": 39.6484, "lon": 27.8826},
    {"name": "Bilecik", "lat": 40.1426, "lon": 29.9793},
    {"name": "Bingol", "lat": 38.8855, "lon": 40.4980},
    {"name": "Bitlis", "lat": 38.4006, "lon": 42.1095},
    {"name": "Bolu", "lat": 40.7395, "lon": 31.6116},
    {"name": "Burdur", "lat": 37.7203, "lon": 30.2908},
    {"name": "Bursa", "lat": 40.1885, "lon": 29.0610},
    {"name": "Canakkale", "lat": 40.1553, "lon": 26.4142},
    {"name": "Cankiri", "lat": 40.6013, "lon": 33.6134},
    {"name": "Corum", "lat": 40.5506, "lon": 34.9556},
    {"name": "Denizli", "lat": 37.7765, "lon": 29.0864},
    {"name": "Diyarbakir", "lat": 37.9144, "lon": 40.2306},
    {"name": "Edirne", "lat": 41.6771, "lon": 26.5557},
    {"name": "Elazig", "lat": 38.6810, "lon": 39.2264},
    {"name": "Erzincan", "lat": 39.7500, "lon": 39.5000},
    {"name": "Erzurum", "lat": 39.9000, "lon": 41.2700},
    {"name": "Eskisehir", "lat": 39.7767, "lon": 30.5206},
    {"name": "Gaziantep", "lat": 37.0662, "lon": 37.3833},
    {"name": "Giresun", "lat": 40.9128, "lon": 38.3895},
    {"name": "Gumushane", "lat": 40.4603, "lon": 39.4814},
    {"name": "Hakkari", "lat": 37.5833, "lon": 43.7333},
    {"name": "Hatay", "lat": 36.2021, "lon": 36.1606},
    {"name": "Isparta", "lat": 37.7648, "lon": 30.5566},
    {"name": "Mersin", "lat": 36.8000, "lon": 34.6333},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784},
    {"name": "Izmir", "lat": 38.4237, "lon": 27.1428},
    {"name": "Kars", "lat": 40.6167, "lon": 43.1000},
    {"name": "Kastamonu", "lat": 41.3887, "lon": 33.7827},
    {"name": "Kayseri", "lat": 38.7312, "lon": 35.4787},
    {"name": "Kirklareli", "lat": 41.7355, "lon": 27.2252},
    {"name": "Kirsehir", "lat": 39.1458, "lon": 34.1605},
    {"name": "Kocaeli", "lat": 40.8533, "lon": 29.8815},
    {"name": "Konya", "lat": 37.8746, "lon": 32.4932},
    {"name": "Kutahya", "lat": 39.4167, "lon": 29.9833},
    {"name": "Malatya", "lat": 38.3552, "lon": 38.3095},
    {"name": "Manisa", "lat": 38.6191, "lon": 27.4289},
    {"name": "Kahramanmaras", "lat": 37.5858, "lon": 36.9371},
    {"name": "Mardin", "lat": 37.3122, "lon": 40.7351},
    {"name": "Mugla", "lat": 37.2153, "lon": 28.3636},
    {"name": "Mus", "lat": 38.9462, "lon": 41.7539},
    {"name": "Nevsehir", "lat": 38.6244, "lon": 34.7239},
    {"name": "Nigde", "lat": 37.9667, "lon": 34.6833},
    {"name": "Ordu", "lat": 40.9839, "lon": 37.8764},
    {"name": "Rize", "lat": 41.0201, "lon": 40.5234},
    {"name": "Sakarya", "lat": 40.7569, "lon": 30.3781},
    {"name": "Samsun", "lat": 41.2867, "lon": 36.3300},
    {"name": "Siirt", "lat": 37.9333, "lon": 41.9500},
    {"name": "Sinop", "lat": 42.0264, "lon": 35.1551},
    {"name": "Sivas", "lat": 39.7477, "lon": 37.0179},
    {"name": "Tekirdag", "lat": 40.9833, "lon": 27.5167},
    {"name": "Tokat", "lat": 40.3167, "lon": 36.5500},
    {"name": "Trabzon", "lat": 41.0015, "lon": 39.7178},
    {"name": "Tunceli", "lat": 39.1083, "lon": 39.5471},
    {"name": "Sanliurfa", "lat": 37.1674, "lon": 38.7955},
    {"name": "Usak", "lat": 38.6823, "lon": 29.4082},
    {"name": "Van", "lat": 38.4891, "lon": 43.4089},
    {"name": "Yozgat", "lat": 39.8181, "lon": 34.8147},
    {"name": "Zonguldak", "lat": 41.4564, "lon": 31.7987},
    {"name": "Aksaray", "lat": 38.3687, "lon": 34.0370},
    {"name": "Bayburt", "lat": 40.2552, "lon": 40.2249},
    {"name": "Karaman", "lat": 37.1811, "lon": 33.2150},
    {"name": "Kirikkale", "lat": 39.8468, "lon": 33.5153},
    {"name": "Batman", "lat": 37.8812, "lon": 41.1351},
    {"name": "Sirnak", "lat": 37.4187, "lon": 42.4918},
    {"name": "Bartin", "lat": 41.6358, "lon": 32.3375},
    {"name": "Ardahan", "lat": 41.1105, "lon": 42.7022},
    {"name": "Igdir", "lat": 39.9167, "lon": 44.0333},
    {"name": "Yalova", "lat": 40.6500, "lon": 29.2667},
    {"name": "Karabuk", "lat": 41.2061, "lon": 32.6204},
    {"name": "Kilis", "lat": 36.7184, "lon": 37.1212},
    {"name": "Osmaniye", "lat": 37.0742, "lon": 36.2461},
    {"name": "Duzce", "lat": 40.8438, "lon": 31.1565},
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
            "map_tab": "Turkey Map",
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
        "map_tab": "Turkiye Haritasi",
    }


def get_ski_texts(lang):
    if lang == "en":
        return {
            "title": "Ski Resort Snow Depth",
            "subtitle": "Current modeled snow depth and live report links for major resorts.",
            "depth": "Current Snow Depth",
            "updated": "Updated",
            "open_report": "More Info",
            "back": "Back To Weather",
            "unavailable": "Data unavailable",
        }

    return {
        "title": "Kayak Merkezleri Kar Birikimi",
        "subtitle": "Buyuk merkezler icin anlik model kar birikimi ve canli rapor baglantisi.",
        "depth": "Guncel Kar Birikimi",
        "updated": "Guncellendi",
        "open_report": "Daha Fazla Bilgi",
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
    return _get_json(url)


def get_ski_resorts_snow_data(lang="tr"):
    now = time.time()
    if _SKI_CACHE["items"] and (now - _SKI_CACHE["ts"]) < _SKI_CACHE_TTL:
        return _SKI_CACHE["items"]

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

    _SKI_CACHE["ts"] = time.time()
    _SKI_CACHE["items"] = items
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
    rain_like_codes = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}

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
        today_has_rain_code = today.get("weather_code") in rain_like_codes
        if rain_mm is not None:
            if rain_mm > 0 and today_has_rain_code:
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
        has_rain_code_next_hours = any(item.get("weather_code") in rain_like_codes for item in next_hours)
        if peak_rain > 0 and has_rain_code_next_hours:
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

    cache_key = _normalize_text(query)
    cached = _LOCATIONS_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - cached[0]) < _LOCATIONS_CACHE_TTL:
        return jsonify(cached[1])

    try:
        items = suggest_locations(query, limit=12)
    except Exception:
        items = []

    _LOCATIONS_CACHE[cache_key] = (time.time(), items)

    return jsonify(items)


@app.route("/", methods=["GET", "POST"])
def index():
    city = request.form.get("city") or request.args.get("city") or "Istanbul"
    lang = (request.form.get("lang") or request.args.get("lang") or "tr").strip().lower()
    if lang not in {"tr", "en"}:
        lang = "tr"
    ui_texts = get_ui_texts(lang)

    try:
        bundle = get_weather_bundle(city, hours=24, days=5, lang=lang)
        weather = bundle.get("weather") or {}
        forecast = bundle.get("forecast", [])
        hourly = bundle.get("hourly", [])
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


@app.route("/turkiye-haritasi", methods=["GET"])
def turkey_map():
    lang = (request.args.get("lang") or "tr").strip().lower()
    if lang not in {"tr", "en"}:
        lang = "tr"
    return render_template(
        "turkey_map.html",
        lang=lang,
        ui_texts=get_ui_texts(lang),
        provinces=TURKEY_PROVINCES,
    )


@app.route("/api/province-weather", methods=["GET"])
def province_weather():
    city = (request.args.get("city") or "").strip()
    lang = (request.args.get("lang") or "tr").strip().lower()
    if lang not in {"tr", "en"}:
        lang = "tr"

    if not city:
        return jsonify({"error": "city is required"}), 400

    cache_key = f"{_normalize_text(city)}|{lang}"
    cached = _PROVINCE_WEATHER_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - cached[0]) < _PROVINCE_WEATHER_CACHE_TTL:
        return jsonify(cached[1])

    try:
        weather = get_current_weather(city)
        weather["description"] = get_weather_description(weather.get("weather_code"), lang=lang)
        payload = {
            "city": weather.get("city") or city,
            "temperature": weather.get("temperature"),
            "felt_temperature": weather.get("felt_temperature"),
            "humidity": weather.get("humidity"),
            "wind_speed": weather.get("wind_speed"),
            "description": weather.get("description"),
        }
        _PROVINCE_WEATHER_CACHE[cache_key] = (time.time(), payload)
        return jsonify(payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    start_server()
