import json
import unicodedata
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

WEATHER_CODES_TR = {
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

WEATHER_CODES_EN = {
    0: "Clear",
    1: "Mostly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Light Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Light Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Light Showers",
    81: "Moderate Showers",
    82: "Violent Showers",
    85: "Light Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm With Hail",
    99: "Severe Thunderstorm With Hail",
}


def get_weather_description(code, lang="tr"):
    if lang == "en":
        return WEATHER_CODES_EN.get(code, "Unknown")
    return WEATHER_CODES_TR.get(code, "Bilinmeyen")


def get_icon_name_for_code(code, hour=None):
    is_night = hour is not None and (hour >= 19 or hour < 5)
    if code in (0, 1):
        return "moon" if is_night else "sun"
    if code == 2:
        return "partly_cloudy"
    if code in (3, 45, 48):
        return "cloud"
    if code in (56, 57, 66, 67):
        return "sleet"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm_rain"
    return "moon" if is_night else "sun"


def get_wind_direction_text(degrees):
    if degrees is None:
        return None

    try:
        value = float(degrees) % 360
    except (TypeError, ValueError):
        return None

    directions = [
        "Kuzey",
        "Kuzeydoğu",
        "Doğu",
        "Güneydoğu",
        "Güney",
        "Güneybatı",
        "Batı",
        "Kuzeybatı",
    ]
    index = int((value + 22.5) // 45) % 8
    return directions[index]


def get_wind_direction_arrow(degrees):
    if degrees is None:
        return None

    try:
        value = float(degrees) % 360
    except (TypeError, ValueError):
        return None

    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    index = int((value + 22.5) // 45) % 8
    return arrows[index]


def get_rain_intensity_style(mm_amount, period="hourly", lang="tr"):
    if mm_amount is None:
        return None, None

    try:
        mm = float(mm_amount)
    except (TypeError, ValueError):
        return None, None

    if mm <= 0:
        return None, None

    if lang == "en":
        if mm < 5:
            return "Light Rain", "rain_1drop"
        if mm < 20:
            return "Rainy", "rain_3drop"
        if mm < 50:
            return "Heavy Rain", "rain_5drop"
        return "Extreme Heavy Rain", "rain_10drop"

    if mm < 5:
        return "Hafif Yağmur", "rain_1drop"
    if mm < 20:
        return "Yağmurlu", "rain_3drop"
    if mm < 50:
        return "Kuvvetli Yağmur", "rain_5drop"
    return "Aşırı Kuvvetli Yağmur", "rain_10drop"


def get_thunder_rain_description(mm_amount, lang="tr"):
    if mm_amount is None:
        return "Thunder Rain" if lang == "en" else "Gök Gürültülü Yağmur"

    try:
        mm = float(mm_amount)
    except (TypeError, ValueError):
        return "Thunder Rain" if lang == "en" else "Gök Gürültülü Yağmur"

    if mm <= 0:
        return "Thunder Rain" if lang == "en" else "Gök Gürültülü Yağmur"
    if lang == "en":
        if mm < 20:
            return "Thunder Light Rain"
        if mm < 50:
            return "Thunder Heavy Rain"
        return "Thunder Extreme Heavy Rain"

    if mm < 20:
        return "Gök Gürültülü Hafif Yağmur"
    if mm < 50:
        return "Gök Gürültülü Kuvvetli Yağmur"
    return "Gök Gürültülü Aşırı Kuvvetli Yağmur"


def get_snow_intensity_style(cm_amount, period="hourly", lang="tr"):
    if cm_amount is None:
        return None, None

    try:
        cm = float(cm_amount)
    except (TypeError, ValueError):
        return None, None

    if cm <= 0:
        return None, None

    if lang == "en":
        if cm < 5:
            return "Light Snow", "snow_1flake"
        if cm < 20:
            return "Snowy", "snow_3flake"
        if cm < 50:
            return "Heavy Snow", "snow_5flake"
        return "Intense Snow", "snow_10flake"

    if cm < 5:
        return "Hafif Karlı", "snow_1flake"
    if cm < 20:
        return "Karlı", "snow_3flake"
    if cm < 50:
        return "Kuvvetli Kar", "snow_5flake"
    return "Yoğun Kar", "snow_10flake"


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


def get_hourly_weather(city_name, hours=24, lang="tr"):
    city = search_city(city_name)
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&hourly=temperature_2m,weather_code,wind_speed_10m,precipitation_probability,precipitation,snowfall"
        f"&forecast_hours={hours}"
        "&timezone=auto&language=tr"
        "&models=ecmwf_ifs025"
    )
    data = _get_json(url)
    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    codes = hourly.get("weather_code") or []
    winds = hourly.get("wind_speed_10m") or []
    precip = hourly.get("precipitation_probability") or []
    precip_mm_values = hourly.get("precipitation") or []
    snow_cm_values = hourly.get("snowfall") or []

    rain_like_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
    thunder_like_codes = {95, 96, 99}
    snow_like_codes = {71, 73, 75, 77, 85, 86}

    now_str = (data.get("current_weather") or {}).get("time") or ""
    current_hour = now_str[:13] if now_str else ""

    result = []
    started = False
    for i, t in enumerate(times):
        if not started:
            if t[:13] >= current_hour or not current_hour:
                started = True
            else:
                continue
        code = codes[i] if i < len(codes) else 0
        hour_label = t[11:16] if len(t) >= 16 else t
        try:
            hour_int = int(t[11:13]) if len(t) >= 13 else None
        except ValueError:
            hour_int = None
        precip_mm = precip_mm_values[i] if i < len(precip_mm_values) else None
        snow_cm = snow_cm_values[i] if i < len(snow_cm_values) else None
        description = get_weather_description(code, lang=lang)
        icon_name = get_icon_name_for_code(code, hour=hour_int)
        rain_intensity_text, rain_intensity_icon = get_rain_intensity_style(
            precip_mm, period="hourly", lang=lang
        )
        if code in rain_like_codes and rain_intensity_text:
            description = rain_intensity_text
            icon_name = rain_intensity_icon or icon_name
        elif code in thunder_like_codes:
            description = get_thunder_rain_description(precip_mm, lang=lang)
            if rain_intensity_icon:
                icon_name = rain_intensity_icon
        snow_intensity_text, snow_intensity_icon = get_snow_intensity_style(
            snow_cm, period="hourly", lang=lang
        )
        if code in snow_like_codes and snow_intensity_text:
            description = snow_intensity_text
            icon_name = snow_intensity_icon or icon_name
        result.append({
            "time": hour_label,
            "temperature": temps[i] if i < len(temps) else None,
            "weather_code": code,
            "description": description,
            "icon_name": icon_name,
            "wind_speed": winds[i] if i < len(winds) else None,
            "precipitation_probability": precip[i] if i < len(precip) else None,
            "precipitation_mm": precip_mm,
            "snowfall_cm": snow_cm,
        })
        if len(result) >= hours:
            break

    return result


def get_current_weather(city_name):
    city = search_city(city_name)
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m"
        "&timezone=auto&language=tr"
        "&models=ecmwf_ifs025"
    )
    data = _get_json(weather_url)
    current = data.get("current") or {}

    return {
        "city": city["name"],
        "admin1": city.get("admin1"),
        "admin2": city.get("admin2"),
        "country": city["country"],
        "temperature": current.get("temperature_2m"),
        "felt_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "wind_direction_text": get_wind_direction_text(current.get("wind_direction_10m")),
        "wind_direction_arrow": get_wind_direction_arrow(current.get("wind_direction_10m")),
        "weather_code": current.get("weather_code"),
        "icon_name": get_icon_name_for_code(current.get("weather_code")),
    }


def get_forecast_weather(city_name, days=5, lang="tr"):
    city = search_city(city_name)
    forecast_url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum"
        f"&forecast_days={days}"
        "&timezone=auto&language=tr"
        "&models=ecmwf_ifs025"
    )
    data = _get_json(forecast_url)
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []
    precip_sum = daily.get("precipitation_sum") or []
    snow_sum = daily.get("snowfall_sum") or []

    rain_like_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
    thunder_like_codes = {95, 96, 99}
    snow_like_codes = {71, 73, 75, 77, 85, 86}

    forecast = []
    for index, date_text in enumerate(times):
        code = codes[index] if index < len(codes) else 0
        day_precip_mm = precip_sum[index] if index < len(precip_sum) else None
        day_snow_cm = snow_sum[index] if index < len(snow_sum) else None
        description = get_weather_description(code, lang=lang)
        icon_name = get_icon_name_for_code(code)
        rain_intensity_text, rain_intensity_icon = get_rain_intensity_style(
            day_precip_mm, period="daily", lang=lang
        )
        if code in rain_like_codes and rain_intensity_text:
            description = rain_intensity_text
            icon_name = rain_intensity_icon or icon_name
        elif code in thunder_like_codes:
            description = get_thunder_rain_description(day_precip_mm, lang=lang)
            if rain_intensity_icon:
                icon_name = rain_intensity_icon
        snow_intensity_text, snow_intensity_icon = get_snow_intensity_style(
            day_snow_cm, period="daily", lang=lang
        )
        if code in snow_like_codes and snow_intensity_text:
            description = snow_intensity_text
            icon_name = snow_intensity_icon or icon_name
        forecast.append(
            {
                "date": date_text,
                "day_name": _get_day_name(date_text),
                "weather_code": code,
                "description": description,
                "max_temp": max_temps[index],
                "min_temp": min_temps[index],
                "icon_name": icon_name,
                "precipitation_sum_mm": day_precip_mm,
                "snowfall_sum_cm": day_snow_cm,
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
    wind_direction_text = weather.get("wind_direction_text") or "Bilinmiyor"
    return (
        f"{weather['city']}, {weather['country']}\n"
        f"Sıcaklık: {weather['temperature']} °C\n"
        f"Nem: {weather['humidity']} %\n"
        f"Rüzgar: {weather['wind_speed']} km/s, {wind_direction_text}\n"
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
