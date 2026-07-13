import unittest

from app import build_daily_summary


class DailySummaryTests(unittest.TestCase):
    def test_flood_warning_added_for_daily_rain_over_50mm(self):
        weather = {"temperature": 20, "description": "Yağmurlu", "wind_speed": 10}
        forecast = [{"max_temp": 24, "min_temp": 18, "precipitation_sum_mm": 51, "snowfall_sum_cm": 0}]
        hourly = [{"precipitation_mm": 1.0, "snowfall_cm": 0, "temperature": 20}]

        summary = build_daily_summary(weather, forecast, hourly)

        self.assertIn("Sel ve taşkın ihtimaline dikkat.", summary)

    def test_snow_warning_added_when_snow_expected(self):
        weather = {"temperature": 0, "description": "Kar yağışlı", "wind_speed": 8}
        forecast = [{"max_temp": 2, "min_temp": -2, "precipitation_sum_mm": 0, "snowfall_sum_cm": 4}]
        hourly = [{"precipitation_mm": 0, "snowfall_cm": 1.2, "temperature": 0}]

        summary = build_daily_summary(weather, forecast, hourly)

        self.assertIn("Yollar kapanabilir, kar lastiği ve zincir takınız mutlaka.", summary)


if __name__ == "__main__":
    unittest.main()
