import sys

from gui_app import run_gui
from weather_app import format_weather_report, get_current_weather


def main():
    city = " ".join(sys.argv[1:]).strip()

    if not city:
        run_gui()
        return

    try:
        weather = get_current_weather(city)
        print(format_weather_report(weather))
    except Exception as exc:
        print(f"Hata: {exc}")


if __name__ == "__main__":
    main()
