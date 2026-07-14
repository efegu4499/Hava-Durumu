import json
import math
import os
import time
import unicodedata
from copy import deepcopy
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_JSON_CACHE = {}
_JSON_CACHE_TTL_SECONDS = 120
_BUNDLE_CACHE = {}
_BUNDLE_CACHE_TTL_SECONDS = 30

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


def calculate_feels_like_c(temp_c, humidity_percent=None, wind_speed_ms=None):
    temp = _to_float(temp_c)
    humidity = _to_float(humidity_percent)
    wind_ms = _to_float(wind_speed_ms)

    if temp is None:
        return None

    # Heat index approximation for warm and humid conditions.
    if humidity is not None and temp >= 27:
        temp_f = (temp * 9.0 / 5.0) + 32.0
        hi_f = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * humidity
            - 0.22475541 * temp_f * humidity
            - 0.00683783 * temp_f * temp_f
            - 0.05481717 * humidity * humidity
            + 0.00122874 * temp_f * temp_f * humidity
            + 0.00085282 * temp_f * humidity * humidity
            - 0.00000199 * temp_f * temp_f * humidity * humidity
        )
        return round((hi_f - 32.0) * 5.0 / 9.0, 1)

    # Wind chill approximation for cold and windy conditions.
    if wind_ms is not None and temp <= 10:
        wind_kmh = max(wind_ms * 3.6, 0.0)
        if wind_kmh >= 4.8:
            wind_term = wind_kmh ** 0.16
            wc = 13.12 + 0.6215 * temp - 11.37 * wind_term + 0.3965 * temp * wind_term
            return round(wc, 1)

    return round(temp, 1)


def _compute_apparent_temperature_c(temp_c, humidity_percent=None, wind_speed_ms=None):
    temp = _to_float(temp_c)
    humidity = _to_float(humidity_percent)
    wind_ms = _to_float(wind_speed_ms)
    if temp is None or humidity is None or wind_ms is None:
        return None

    # Australian Bureau of Meteorology apparent temperature (C).
    vapor_pressure = (humidity / 100.0) * 6.105 * math.exp((17.27 * temp) / (237.7 + temp))
    apparent = temp + 0.33 * vapor_pressure - 0.70 * wind_ms - 4.0
    return round(apparent, 1)


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
    now = time.time()
    cached = _JSON_CACHE.get(url)
    if cached and (now - cached[0]) < _JSON_CACHE_TTL_SECONDS:
        return cached[1]

    request = Request(url, headers={"User-Agent": "gokyra-weather/1.0 (+contact)"})
    retry_delays = [0.45, 0.9, 1.5]
    for attempt, delay in enumerate(retry_delays, start=1):
        try:
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                _JSON_CACHE[url] = (time.time(), data)
                return data
        except HTTPError as exc:
            if exc.code != 429:
                raise

            if cached:
                return cached[1]

            if attempt == len(retry_delays):
                raise ValueError("Servis su anda cok yogun (HTTP 429). Lutfen 30-60 saniye sonra tekrar deneyin.")

            time.sleep(delay)


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


# Alternate source layer (met.no + Nominatim) to avoid Open-Meteo rate limits.
_ALT_GEO_CACHE = {}
_ALT_GEO_CACHE_TTL = 900

_METNO_SYMBOL_TO_CODE = {
    "clearsky": 0,
    "fair": 1,
    "partlycloudy": 2,
    "cloudy": 3,
    "fog": 45,
    "lightrain": 61,
    "rain": 63,
    "heavyrain": 65,
    "lightsleet": 66,
    "sleet": 67,
    "heavysleet": 67,
    "lightsnow": 71,
    "snow": 73,
    "heavysnow": 75,
    "rainshowers": 80,
    "heavyrainshowers": 82,
    "lightsnowshowers": 85,
    "snowshowers": 86,
    "heavysnowshowers": 86,
    "thunder": 95,
    "rainshowersandthunder": 95,
    "heavyrainshowersandthunder": 95,
    "snowshowersandthunder": 96,
}


def _to_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _metno_symbol_to_code(symbol_code):
    if not symbol_code:
        return 3
    key = symbol_code.split("_")[0].lower()
    return _METNO_SYMBOL_TO_CODE.get(key, 3)


def _is_snow_symbol(symbol_code):
    if not symbol_code:
        return False
    return "snow" in symbol_code.split("_")[0].lower()


def _nominatim_search(query_text, limit=10):
    normalized = _normalize_text(query_text)
    now = time.time()
    cached = _ALT_GEO_CACHE.get((normalized, limit))
    if cached and (now - cached[0]) < _ALT_GEO_CACHE_TTL:
        return cached[1]

    params = urlencode(
        {
            "q": query_text,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
            "accept-language": "tr,en",
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    rows = _get_json(url) or []
    out = []
    for row in rows:
        address = row.get("address") or {}
        name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or row.get("name")
            or (row.get("display_name") or "").split(",")[0].strip()
        )
        if not name:
            continue
        item = {
            "name": name,
            "admin1": address.get("state") or address.get("region") or address.get("province"),
            "admin2": address.get("county") or address.get("state_district"),
            "country": address.get("country", "Bilinmiyor"),
            "country_code": (address.get("country_code") or "").upper(),
            "latitude": _to_float(row.get("lat")),
            "longitude": _to_float(row.get("lon")),
        }
        if item["latitude"] is not None and item["longitude"] is not None:
            out.append(item)

    _ALT_GEO_CACHE[(normalized, limit)] = (time.time(), out)
    return out


def _metno_forecast(lat, lon):
    query = urlencode({"lat": lat, "lon": lon})
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?{query}"
    return _get_json(url)


def _get_weatherstack_api_key():
    for key_name in ("WEATHERSTACK_API_KEY", "WEATHERSTACK_ACCESS_KEY", "WEATHERSTACK_KEY"):
        value = (os.getenv(key_name) or "").strip()
        if value:
            return value
    return ""


def _weatherstack_feels_like_temperature(lat, lon):
    api_key = _get_weatherstack_api_key()
    if not api_key:
        return None

    query = urlencode(
        {
            "access_key": api_key,
            "query": f"{lat},{lon}",
            "units": "m",
            # Refresh this value every ~30s instead of being pinned by URL cache.
            "cache_bust": int(time.time() // 30),
        }
    )

    for base_url in (
        "https://api.weatherstack.com/current",
        "http://api.weatherstack.com/current",
    ):
        url = f"{base_url}?{query}"
        try:
            data = _get_json(url)
        except Exception:
            continue

        current = (data or {}).get("current") or {}
        feels_like = _to_float(current.get("feelslike"))
        if feels_like is not None:
            return feels_like

    return None


def _select_felt_temperature(temp_c, humidity_percent, wind_speed_ms, api_apparent_temp):
    value, _ = _select_felt_temperature_with_source(
        temp_c,
        humidity_percent,
        wind_speed_ms,
        api_apparent_temp,
    )
    return value


def _select_felt_temperature_with_source(temp_c, humidity_percent, wind_speed_ms, api_apparent_temp):
    temp = _to_float(temp_c)
    api_value = _to_float(api_apparent_temp)
    computed = _compute_apparent_temperature_c(
        temp,
        humidity_percent=humidity_percent,
        wind_speed_ms=wind_speed_ms,
    )
    if computed is None:
        computed = calculate_feels_like_c(
            temp,
            humidity_percent=humidity_percent,
            wind_speed_ms=wind_speed_ms,
        )

    if api_value is None:
        return computed, "calculated"

    # If upstream apparent value matches air temperature too closely,
    # prefer computed value when it captures wind/humidity impact.
    if temp is not None and abs(api_value - temp) < 0.05:
        if computed is not None and abs(computed - temp) >= 0.1:
            return computed, "calculated"

    return round(api_value, 1), "weatherstack"


def search_city(city_name):
    city_query, location_hint = _split_city_hint(city_name)
    preferred_country_code = _resolve_country_hint(location_hint)
    preferred_admin1 = None if preferred_country_code else _resolve_province_hint(location_hint)
    results = _nominatim_search(city_query, limit=10)

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

    results = _nominatim_search(query, limit=max(24, limit * 2))
    suggestions = []
    seen = set()
    for result in results:
        name = (result.get("name") or "").strip()
        admin1 = (result.get("admin1") or "").strip()
        country = (result.get("country") or "").strip()
        if not name:
            continue
        parts = [name]
        if admin1 and admin1 != name:
            parts.append(admin1)
        if country and country not in parts:
            parts.append(country)
        label = ", ".join(parts)
        if label in seen:
            continue
        seen.add(label)
        value = f"{name}, {admin1}" if admin1 and admin1 != name else name
        suggestions.append({"label": label, "value": value})
        if len(suggestions) >= limit:
            break
    return suggestions


def get_weather_bundle(city_name, hours=24, days=5, lang="tr"):
    cache_key = f"{_normalize_text(city_name)}|{hours}|{days}|{lang}"
    cached_bundle = _BUNDLE_CACHE.get(cache_key)
    now = time.time()
    if cached_bundle and (now - cached_bundle[0]) < _BUNDLE_CACHE_TTL_SECONDS:
        return deepcopy(cached_bundle[1])

    city = search_city(city_name)
    raw = _metno_forecast(city["latitude"], city["longitude"])
    timeseries = ((raw.get("properties") or {}).get("timeseries") or [])
    if not timeseries:
        raise ValueError("Hava verisi alınamadı.")

    current_item = timeseries[0]
    current_data = current_item.get("data") or {}
    current_instant = (current_data.get("instant") or {}).get("details") or {}
    current_symbol = (
        ((current_data.get("next_1_hours") or {}).get("summary") or {}).get("symbol_code")
        or ((current_data.get("next_6_hours") or {}).get("summary") or {}).get("symbol_code")
        or ((current_data.get("next_12_hours") or {}).get("summary") or {}).get("symbol_code")
    )
    current_code = _metno_symbol_to_code(current_symbol)
    wind_dir = _to_float(current_instant.get("wind_from_direction"))
    current_temp = _to_float(current_instant.get("air_temperature"))
    current_humidity = _to_float(current_instant.get("relative_humidity"))
    current_wind_ms = _to_float(current_instant.get("wind_speed"))
    apparent_temp, felt_source = _select_felt_temperature_with_source(
        current_temp,
        current_humidity,
        current_wind_ms,
        _weatherstack_feels_like_temperature(city["latitude"], city["longitude"]),
    )

    weather = {
        "city": city["name"],
        "admin1": city.get("admin1"),
        "admin2": city.get("admin2"),
        "country": city["country"],
        "temperature": current_temp,
        "felt_temperature": apparent_temp,
        "felt_temperature_source": felt_source,
        "humidity": current_humidity,
        "wind_speed": current_wind_ms,
        "wind_direction": wind_dir,
        "wind_direction_text": get_wind_direction_text(wind_dir),
        "wind_direction_arrow": get_wind_direction_arrow(wind_dir),
        "weather_code": current_code,
        "icon_name": get_icon_name_for_code(current_code),
        "description": get_weather_description(current_code, lang=lang),
    }

    rain_like_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
    snow_like_codes = {71, 73, 75, 77, 85, 86}
    thunder_like_codes = {95, 96, 99}

    hourly_result = []
    for item in timeseries[:hours]:
        t = item.get("time") or ""
        data_block = item.get("data") or {}
        instant = (data_block.get("instant") or {}).get("details") or {}
        one_hour = data_block.get("next_1_hours") or {}
        details_1h = one_hour.get("details") or {}
        symbol_code = (one_hour.get("summary") or {}).get("symbol_code")
        code = _metno_symbol_to_code(symbol_code)
        hour_label = t[11:16] if len(t) >= 16 else t
        try:
            hour_int = int(t[11:13]) if len(t) >= 13 else None
        except ValueError:
            hour_int = None

        precip_mm = _to_float(details_1h.get("precipitation_amount"), 0.0)
        snow_cm = round(precip_mm * 0.7, 2) if _is_snow_symbol(symbol_code) else 0.0

        description = get_weather_description(code, lang=lang)
        icon_name = get_icon_name_for_code(code, hour=hour_int)
        rain_text, rain_icon = get_rain_intensity_style(precip_mm, period="hourly", lang=lang)
        if code in rain_like_codes and rain_text:
            description = rain_text
            icon_name = rain_icon or icon_name
        elif code in thunder_like_codes:
            description = get_thunder_rain_description(precip_mm, lang=lang)
            if rain_icon:
                icon_name = rain_icon
        snow_text, snow_icon = get_snow_intensity_style(snow_cm, period="hourly", lang=lang)
        if code in snow_like_codes and snow_text:
            description = snow_text
            icon_name = snow_icon or icon_name

        hourly_result.append(
            {
                "time": hour_label,
                "temperature": _to_float(instant.get("air_temperature")),
                "weather_code": code,
                "description": description,
                "icon_name": icon_name,
                "wind_speed": _to_float(instant.get("wind_speed")),
                "precipitation_probability": None,
                "precipitation_mm": precip_mm,
                "snowfall_cm": snow_cm,
            }
        )

    daily_buckets = {}
    for item in timeseries:
        t = item.get("time") or ""
        day_key = t[:10]
        if not day_key:
            continue
        block = item.get("data") or {}
        instant = (block.get("instant") or {}).get("details") or {}
        one_hour = block.get("next_1_hours") or {}
        details_1h = one_hour.get("details") or {}
        symbol_code = (one_hour.get("summary") or {}).get("symbol_code")
        code = _metno_symbol_to_code(symbol_code)
        temp = _to_float(instant.get("air_temperature"))
        precip = _to_float(details_1h.get("precipitation_amount"), 0.0)
        snow = round(precip * 0.7, 2) if _is_snow_symbol(symbol_code) else 0.0

        bucket = daily_buckets.setdefault(day_key, {"temps": [], "codes": [], "precip": 0.0, "snow": 0.0})
        if temp is not None:
            bucket["temps"].append(temp)
        bucket["codes"].append(code)
        bucket["precip"] += precip
        bucket["snow"] += snow

    forecast = []
    for date_text in sorted(daily_buckets.keys())[:days]:
        b = daily_buckets[date_text]
        code = max(set(b["codes"]), key=b["codes"].count) if b["codes"] else 3
        day_precip_mm = round(b["precip"], 2)
        day_snow_cm = round(b["snow"], 2)
        description = get_weather_description(code, lang=lang)
        icon_name = get_icon_name_for_code(code)
        rain_text, rain_icon = get_rain_intensity_style(day_precip_mm, period="daily", lang=lang)
        if code in rain_like_codes and rain_text:
            description = rain_text
            icon_name = rain_icon or icon_name
        elif code in thunder_like_codes:
            description = get_thunder_rain_description(day_precip_mm, lang=lang)
            if rain_icon:
                icon_name = rain_icon
        snow_text, snow_icon = get_snow_intensity_style(day_snow_cm, period="daily", lang=lang)
        if code in snow_like_codes and snow_text:
            description = snow_text
            icon_name = snow_icon or icon_name

        temps = b["temps"]
        forecast.append(
            {
                "date": date_text,
                "day_name": _get_day_name(date_text),
                "weather_code": code,
                "description": description,
                "max_temp": max(temps) if temps else None,
                "min_temp": min(temps) if temps else None,
                "icon_name": icon_name,
                "precipitation_sum_mm": day_precip_mm,
                "snowfall_sum_cm": day_snow_cm,
            }
        )

    bundle = {"weather": weather, "hourly": hourly_result, "forecast": forecast}
    _BUNDLE_CACHE[cache_key] = (time.time(), bundle)
    return deepcopy(bundle)


def get_current_weather(city_name):
    return get_weather_bundle(city_name, hours=1, days=1, lang="tr").get("weather", {})


def get_hourly_weather(city_name, hours=24, lang="tr"):
    return get_weather_bundle(city_name, hours=hours, days=1, lang=lang).get("hourly", [])


def get_forecast_weather(city_name, days=5, lang="tr"):
    bundle = get_weather_bundle(city_name, hours=1, days=days, lang=lang)
    weather = bundle.get("weather") or {}
    return {
        "city": weather.get("city"),
        "admin1": weather.get("admin1"),
        "admin2": weather.get("admin2"),
        "country": weather.get("country"),
        "forecast": bundle.get("forecast", []),
    }


if __name__ == "__main__":
    try:
        report = get_current_weather("Istanbul")
        print(format_weather_report(report))
    except (HTTPError, URLError, ValueError) as exc:
        print(f"Hata: {exc}")
