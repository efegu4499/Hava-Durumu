import unittest

from app import build_daily_summary


class DailySummaryTests(unittest.TestCase):
    def test_flood_warning_added_for_daily_rain_over_50mm(self):
        weather = {"temperature": 20, "description": "Yağmurlu", "wind_speed": 10}
        forecast = [{"max_temp": 24, "min_temp": 18, "weather_code": 63, "precipitation_sum_mm": 51, "snowfall_sum_cm": 0}]
        hourly = [{"weather_code": 63, "precipitation_mm": 1.0, "snowfall_cm": 0, "temperature": 20}]

        summary = build_daily_summary(weather, forecast, hourly)

        self.assertIn("Sel ve taşkın ihtimaline dikkat.", summary)

    def test_snow_warning_added_for_daily_snow_20cm_or_more(self):
        weather = {"temperature": 0, "description": "Kar yağışlı", "wind_speed": 8}
        forecast = [{"max_temp": 2, "min_temp": -2, "weather_code": 71, "precipitation_sum_mm": 0, "snowfall_sum_cm": 20}]
        hourly = [{"weather_code": 71, "precipitation_mm": 0, "snowfall_cm": 1.2, "temperature": 0}]

        summary = build_daily_summary(weather, forecast, hourly)

        self.assertIn("Yollar kapanabilir, kar lastiği ve zincir takınız mutlaka.", summary)

    def test_snow_warning_not_added_below_20cm_daily_even_if_hourly_snow_exists(self):
        weather = {"temperature": 0, "description": "Kar yağışlı", "wind_speed": 8}
        forecast = [{"max_temp": 2, "min_temp": -2, "weather_code": 71, "precipitation_sum_mm": 0, "snowfall_sum_cm": 19.9}]
        hourly = [{"weather_code": 71, "precipitation_mm": 0, "snowfall_cm": 3.0, "temperature": 0}]

        summary = build_daily_summary(weather, forecast, hourly)

        self.assertNotIn("Yollar kapanabilir, kar lastiği ve zincir takınız mutlaka.", summary)

    def test_low_mm_without_rain_code_does_not_report_rain_expected(self):
        weather = {"temperature": 21, "description": "Parçalı bulutlu", "wind_speed": 5}
        forecast = [{"max_temp": 25, "min_temp": 17, "weather_code": 2, "precipitation_sum_mm": 0.1, "snowfall_sum_cm": 0}]
        hourly = [{"weather_code": 2, "precipitation_mm": 0.1, "snowfall_cm": 0, "temperature": 21}]

        summary = build_daily_summary(weather, forecast, hourly)

        self.assertNotIn("Günlük yağış beklentisi", summary)


if __name__ == "__main__":
    unittest.main()
