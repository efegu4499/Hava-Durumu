import unittest

from weather_app import (
    format_forecast_entry,
    get_icon_name_for_code,
    get_rain_intensity_style,
    get_weather_description,
    pick_best_city_result,
)


class WeatherAppTests(unittest.TestCase):
    def test_clear_sky_code_maps_to_turkish_label(self):
        self.assertEqual(get_weather_description(0), "Açık")

    def test_clear_sky_icon_maps_to_sun(self):
        self.assertEqual(get_icon_name_for_code(0), "sun")

    def test_rain_icon_maps_to_rain(self):
        self.assertEqual(get_icon_name_for_code(61), "rain")

    def test_freezing_rain_icon_maps_to_sleet(self):
        self.assertEqual(get_icon_name_for_code(66), "sleet")

    def test_hourly_light_rain_maps_to_single_drop_icon(self):
        label, icon = get_rain_intensity_style(0.4, period="hourly")
        self.assertEqual(label, "Hafif Şiddetli Yağmur")
        self.assertEqual(icon, "rain_1drop")

    def test_daily_heavy_rain_maps_to_six_drop_icon(self):
        label, icon = get_rain_intensity_style(16, period="daily")
        self.assertEqual(label, "Çok Şiddetli Yağmur")
        self.assertEqual(icon, "rain_6drop")

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
