import unittest
from unittest.mock import patch

from weather_app import (
    _compute_apparent_temperature_c,
    _get_weatherstack_api_key,
    _select_felt_temperature,
    _select_felt_temperature_with_source,
    _weatherstack_feels_like_temperature,
    calculate_feels_like_c,
    format_forecast_entry,
    get_icon_name_for_code,
    get_rain_intensity_style,
    get_thunder_rain_description,
    get_wind_direction_arrow,
    get_snow_intensity_style,
    get_weather_description,
    pick_best_city_result,
)


class WeatherAppTests(unittest.TestCase):
    def test_clear_sky_code_maps_to_turkish_label(self):
        self.assertEqual(get_weather_description(0), "Açık")

    def test_clear_sky_code_maps_to_english_label(self):
        self.assertEqual(get_weather_description(0, lang="en"), "Clear")

    def test_clear_sky_icon_maps_to_sun(self):
        self.assertEqual(get_icon_name_for_code(0), "sun")

    def test_rain_icon_maps_to_rain(self):
        self.assertEqual(get_icon_name_for_code(61), "rain")

    def test_freezing_rain_icon_maps_to_sleet(self):
        self.assertEqual(get_icon_name_for_code(66), "sleet")

    def test_hourly_light_rain_maps_to_single_drop_icon(self):
        label, icon = get_rain_intensity_style(0.4, period="hourly")
        self.assertEqual(label, "Hafif Yağmur")
        self.assertEqual(icon, "rain_1drop")

    def test_daily_heavy_rain_maps_to_six_drop_icon(self):
        label, icon = get_rain_intensity_style(16, period="daily")
        self.assertEqual(label, "Yağmurlu")
        self.assertEqual(icon, "rain_3drop")

    def test_daily_very_heavy_rain_maps_to_ten_drop_icon(self):
        label, icon = get_rain_intensity_style(55, period="daily")
        self.assertEqual(label, "Aşırı Kuvvetli Yağmur")
        self.assertEqual(icon, "rain_10drop")

    def test_thunder_prefix_for_light_rain_description(self):
        self.assertEqual(
            get_thunder_rain_description(2),
            "Gök Gürültülü Hafif Yağmur",
        )

    def test_thunder_prefix_for_light_rain_description_in_english(self):
        self.assertEqual(
            get_thunder_rain_description(2, lang="en"),
            "Thunder Light Rain",
        )

    def test_hourly_light_snow_maps_to_single_flake_icon(self):
        label, icon = get_snow_intensity_style(0.3, period="hourly")
        self.assertEqual(label, "Hafif Karlı")
        self.assertEqual(icon, "snow_1flake")

    def test_daily_heavy_snow_maps_to_six_flake_icon(self):
        label, icon = get_snow_intensity_style(12, period="daily")
        self.assertEqual(label, "Karlı")
        self.assertEqual(icon, "snow_3flake")

    def test_daily_midrange_snow_maps_to_five_flake_icon(self):
        label, icon = get_snow_intensity_style(30, period="daily")
        self.assertEqual(label, "Kuvvetli Kar")
        self.assertEqual(icon, "snow_5flake")

    def test_daily_intense_snow_maps_to_ten_flake_icon(self):
        label, icon = get_snow_intensity_style(55, period="daily")
        self.assertEqual(label, "Yoğun Kar")
        self.assertEqual(icon, "snow_10flake")

    def test_wind_direction_arrow_maps_northeast(self):
        self.assertEqual(get_wind_direction_arrow(45), "↗")

    def test_feels_like_higher_in_hot_humid_conditions(self):
        feels_like = calculate_feels_like_c(33, humidity_percent=75, wind_speed_ms=1)
        self.assertGreater(feels_like, 33)

    def test_feels_like_lower_in_cold_windy_conditions(self):
        feels_like = calculate_feels_like_c(2, humidity_percent=60, wind_speed_ms=8)
        self.assertLess(feels_like, 2)

    def test_apparent_temperature_formula_returns_value(self):
        value = _compute_apparent_temperature_c(28, humidity_percent=70, wind_speed_ms=3)
        self.assertIsNotNone(value)

    @patch("weather_app.os.getenv", return_value="demo-key")
    @patch("weather_app._get_json")
    def test_weatherstack_feels_like_temperature_parses_value(self, mock_get_json, _mock_getenv):
        mock_get_json.return_value = {"current": {"feelslike": 14.6}}
        self.assertEqual(_weatherstack_feels_like_temperature(41.0, 29.0), 14.6)

    @patch("weather_app.os.getenv")
    def test_weatherstack_api_key_reads_fallback_env_names(self, mock_getenv):
        mapping = {
            "WEATHERSTACK_API_KEY": "",
            "WEATHERSTACK_ACCESS_KEY": "access-demo",
            "WEATHERSTACK_KEY": "",
        }
        mock_getenv.side_effect = lambda name: mapping.get(name, "")
        self.assertEqual(_get_weatherstack_api_key(), "access-demo")

    @patch("weather_app.os.getenv", return_value="demo-key")
    @patch("weather_app._get_json")
    def test_weatherstack_feels_like_temperature_fallbacks_on_error(self, mock_get_json, _mock_getenv):
        mock_get_json.side_effect = RuntimeError("network")
        self.assertIsNone(_weatherstack_feels_like_temperature(41.0, 29.0))

    @patch("weather_app.os.getenv", return_value="")
    def test_weatherstack_feels_like_temperature_returns_none_without_api_key(self, _mock_getenv):
        self.assertIsNone(_weatherstack_feels_like_temperature(41.0, 29.0))

    def test_select_felt_temperature_uses_computed_when_api_equals_temp(self):
        value = _select_felt_temperature(2, 65, 8, 2)
        self.assertLess(value, 2)

    def test_select_felt_temperature_keeps_api_when_meaningfully_different(self):
        value = _select_felt_temperature(22, 55, 3, 25.2)
        self.assertEqual(value, 25.2)

    def test_select_felt_temperature_with_source_reports_weatherstack(self):
        value, source = _select_felt_temperature_with_source(22, 55, 3, 25.2)
        self.assertEqual(value, 25.2)
        self.assertEqual(source, "weatherstack")

    def test_aliağa_prefers_turkey_match_over_spanish_alias(self):
        results = [
            {
                "name": "Aliaga",
                "country": "İspanya",
                "country_code": "ES",
                "latitude": 40.67411,
                "longitude": -0.70333,
            },
            {
                "name": "Aliağa",
                "country": "Türkiye Cumhuriyeti",
                "country_code": "TR",
                "latitude": 38.79975,
                "longitude": 26.97203,
            },
        ]
        selected = pick_best_city_result("Aliağa", results)
        self.assertEqual(selected["country_code"], "TR")
        self.assertEqual(selected["name"], "Aliağa")

    def test_sample_forecast_format(self):
        self.assertEqual(
            format_forecast_entry("Pazartesi", "İzmir", 32, "Bulutlu"),
            "Pazartesi - İzmir: 32°C, Bulutlu",
        )


if __name__ == "__main__":
    unittest.main()
