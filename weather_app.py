import json
import unicodedata
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

WEATHER_CODES = {
    0: "Açık",
    1: "Çoğunlukla Açık",
    2: "Parçalı Bulutlu",
    3: "Kapalı",
    45: "Sisli",
    48: "Dondurucu Sis",
    51: "Hafif Çiseleme",
    53: "Orta Şiddetli Çiseleme",
    55: "Yoğun Çiseleme",
    56: "Buzlu Hafif Çiseleme",
    57: "Buzlu Yoğun Çiseleme",
    61: "Hafif Yağmur",
    63: "Orta Yağmur",
    65: "Şiddetli Yağmur",
    66: "Hafif Dondurucu Yağmur",
    67: "Şiddetli Dondurucu Yağmur",
    71: "Hafif Kar",
    73: "Orta Kar",
    75: "Şiddetli Kar",
    77: "Kar Taneleri",
    80: "Hafif Sağanak",
    81: "Orta Sağanak",
    82: "Şiddetli Sağanak",
    85: "Hafif Kar Yağışı",
    86: "Şiddetli Kar Yağışı",
    95: "Gök Gürültülü Fırtına",
    96: "Dolu İçeren Fırtına",
    99: "Şiddetli Dolu İçeren Fırtına",
}


def get_weather_description(code):
    return WEATHER_CODES.get(code, "Bilinmeyen")


def get_icon_name_for_code(code):
    if code in (0, 1):
        return "sun"
    if code in (2, 3, 45, 48):
        return "cloud"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    return "sun"


def _get_day_name(date_text):
    day_map = {
        "Mon": "Pzt",
        "Tue": "Sal",
        "Wed": "Çar",
        "Thu": "Per",
        "Fri": "Cum",
        "Sat": "Cmt",
        "Sun": "Paz",
    }
    return day_map.get(datetime.fromisoformat(date_text).strftime("%a"), "--")


def _get_json(url):
    request = Request(url, headers={"User-Agent": "weather-app/1.0"})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_text(value):
    normalized = unicodedata.normalize("NFKD", (value or ""))
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return (
        without_marks.lower()
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
        .strip()
    )


def _split_city_hint(city_name):
    if "," not in city_name:
        return city_name.strip(), None

    city_part, location_hint = city_name.split(",", 1)
    return city_part.strip(), location_hint.strip()


def _resolve_country_hint(country_hint):
    if not country_hint:
        return None

    normalized_hint = _normalize_text(country_hint)
    if normalized_hint in {"turkiye", "turkey", "tr"}:
        return "TR"
    if normalized_hint in {"ispanya", "spain", "es"}:
        return "ES"
    return None


def _resolve_province_hint(location_hint):
    if not location_hint:
        return None
    return _normalize_text(location_hint)


def pick_best_city_result(
    city_name,
    results,
    preferred_country_code=None,
    preferred_admin1=None,
):
    city_name, _ = _split_city_hint(city_name)
    normalized_query = _normalize_text(city_name)
    preferred_admin1 = _normalize_text(preferred_admin1) if preferred_admin1 else None
    score_by_result = []

    for result in results:
        name = (result.get("name") or "").strip()
        normalized_name = _normalize_text(name)
        admin1 = _normalize_text(result.get("admin1") or "")
        country_code = (result.get("country_code") or "").upper()
        country = (result.get("country") or "").lower()

        score = 0
        if normalized_name == normalized_query:
            score += 12
        elif normalized_query in normalized_name:
            score += 7
        elif normalized_name in normalized_query:
            score += 5

        if preferred_country_code and country_code == preferred_country_code:
            score += 15
        if preferred_admin1 and admin1 == preferred_admin1:
            score += 12
        elif preferred_admin1 and preferred_admin1 in admin1:
            score += 6
        if country_code == "TR":
            score += 8
        if "türkiye" in country or "turkiye" in country:
            score += 6
        if country_code in {"ES", "GR", "PH"}:
            score -= 1

        score_by_result.append((score, result))

    if not score_by_result:
        return None

    score_by_result.sort(key=lambda item: item[0], reverse=True)
    return score_by_result[0][1]


def search_city(city_name):
    city_query, location_hint = _split_city_hint(city_name)
    preferred_country_code = _resolve_country_hint(location_hint)
    preferred_admin1 = None if preferred_country_code else _resolve_province_hint(location_hint)
    query = quote(city_query)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=10&language=tr&format=json"
    data = _get_json(url)
    results = data.get("results") or []

    if not results:
        raise ValueError(f"{city_name} için şehir bulunamadı.")

    result = pick_best_city_result(
        city_query,
        results,
        preferred_country_code=preferred_country_code,
        preferred_admin1=preferred_admin1,
    )
    if not result:
        result = results[0]

    return {
        "name": result["name"],
        "admin1": result.get("admin1"),
        "admin2": result.get("admin2"),
        "country": result.get("country", "Bilinmiyor"),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }


def suggest_locations(query_text, limit=12):
    query = (query_text or "").strip()
    if len(query) < 2:
        return []

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(query)}&count=30&language=tr&format=json"
    data = _get_json(url)
    results = data.get("results") or []

    suggestions = []
    seen = set()
    for result in results:
        if result.get("country_code") != "TR":
            continue

        name = (result.get("name") or "").strip()
        admin1 = (result.get("admin1") or "").strip()
        if not name:
            continue

        label = f"{name}, {admin1}" if admin1 and admin1 != name else name
        if label in seen:
            continue

        seen.add(label)
        suggestions.append({"label": label, "value": label})
        if len(suggestions) >= limit:
            break

    return suggestions


def get_current_weather(city_name):
    city = search_city(city_name)
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        "&timezone=auto&language=tr"
    )
    data = _get_json(weather_url)
    current = data.get("current") or {}

    return {
        "city": city["name"],
        "admin1": city.get("admin1"),
        "admin2": city.get("admin2"),
        "country": city["country"],
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "icon_name": get_icon_name_for_code(current.get("weather_code")),
    }


def get_forecast_weather(city_name, days=5):
    city = search_city(city_name)
    forecast_url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        f"&forecast_days={days}"
        "&timezone=auto&language=tr"
    )
    data = _get_json(forecast_url)
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []

    forecast = []
    for index, date_text in enumerate(times):
        description = get_weather_description(codes[index])
        forecast.append(
            {
                "date": date_text,
                "day_name": _get_day_name(date_text),
                "weather_code": codes[index],
                "description": description,
                "max_temp": max_temps[index],
                "min_temp": min_temps[index],
                "icon_name": get_icon_name_for_code(codes[index]),
            }
        )

    return {
        "city": city["name"],
        "admin1": city.get("admin1"),
        "admin2": city.get("admin2"),
        "country": city["country"],
        "forecast": forecast,
    }


def format_forecast_lines(forecast_weather):
    lines = []
    for item in forecast_weather.get("forecast", []):
        description = get_weather_description(item["weather_code"])
        lines.append(
            f"{item['day_name']} - {item['max_temp']}°C / {item['min_temp']}°C - {description}"
        )
    return "\n".join(lines)


def format_weather_report(weather):
    code = weather["weather_code"]
    description = get_weather_description(code)
    return (
        f"{weather['city']}, {weather['country']}\n"
        f"Sıcaklık: {weather['temperature']} °C\n"
        f"Nem: {weather['humidity']} %\n"
        f"Rüzgar: {weather['wind_speed']} km/s\n"
        f"Durum: {description}"
    )


def format_forecast_entry(day_name, city_name, temperature, description):
    return f"{day_name} - {city_name}: {temperature}°C, {description}"


def get_example_weather_report():
    return format_forecast_entry("Pazartesi", "İzmir", 32, "Bulutlu")


if __name__ == "__main__":
    try:
        report = get_current_weather("Istanbul")
        print(format_weather_report(report))
    except (HTTPError, URLError, ValueError) as exc:
        print(f"Hata: {exc}")
