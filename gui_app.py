from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageDraw

from weather_app import (
    get_current_weather,
    get_forecast_weather,
    get_weather_description,
    format_forecast_lines,
    get_icon_name_for_code,
)


ASSET_DIR = Path(__file__).with_name("assets")
BACKGROUND_IMAGE = ASSET_DIR / "weather_bg.gif"
WEATHER_ICON_FILES = {
    "sun": ASSET_DIR / "sun.gif",
    "moon": ASSET_DIR / "moon.gif",
    "cloud": ASSET_DIR / "cloud.gif",
    "partly_cloudy": ASSET_DIR / "partly_cloudy.gif",
    "rain": ASSET_DIR / "rain.gif",
    "rain_1drop": ASSET_DIR / "rain_1drop.gif",
    "rain_3drop": ASSET_DIR / "rain_3drop.gif",
    "rain_6drop": ASSET_DIR / "rain_6drop.gif",
    "snow": ASSET_DIR / "snow.gif",
    "snow_1flake": ASSET_DIR / "snow_1flake.gif",
    "snow_3flake": ASSET_DIR / "snow_3flake.gif",
    "snow_6flake": ASSET_DIR / "snow_6flake.gif",
    "sleet": ASSET_DIR / "sleet.gif",
    "storm": ASSET_DIR / "storm.gif",
    "storm_rain": ASSET_DIR / "storm_rain.gif",
}


def _create_icon_image(path, kind):
    image = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if kind == "sun":
        draw.ellipse((20, 20, 100, 100), fill="#ffd84d")
        draw.line((60, 8, 60, 0), fill="#ffd84d", width=6)
        draw.line((60, 120, 60, 112), fill="#ffd84d", width=6)
        draw.line((8, 60, 0, 60), fill="#ffd84d", width=6)
        draw.line((120, 60, 112, 60), fill="#ffd84d", width=6)
        draw.line((18, 18, 10, 10), fill="#ffd84d", width=6)
        draw.line((102, 18, 110, 10), fill="#ffd84d", width=6)
        draw.line((18, 102, 10, 110), fill="#ffd84d", width=6)
        draw.line((102, 102, 110, 110), fill="#ffd84d", width=6)
    elif kind == "cloud":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
    elif kind == "rain":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((30, 96, 24, 112), fill="#4da3ff", width=4)
        draw.line((52, 96, 46, 112), fill="#4da3ff", width=4)
        draw.line((74, 96, 68, 112), fill="#4da3ff", width=4)
    elif kind == "rain_1drop":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((60, 94, 54, 112), fill="#4da3ff", width=5)
    elif kind == "rain_3drop":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((30, 96, 24, 112), fill="#4da3ff", width=4)
        draw.line((52, 96, 46, 112), fill="#4da3ff", width=4)
        draw.line((74, 96, 68, 112), fill="#4da3ff", width=4)
    elif kind == "rain_6drop":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((22, 94, 16, 112), fill="#4da3ff", width=4)
        draw.line((38, 94, 32, 112), fill="#4da3ff", width=4)
        draw.line((54, 94, 48, 112), fill="#4da3ff", width=4)
        draw.line((70, 94, 64, 112), fill="#4da3ff", width=4)
        draw.line((86, 94, 80, 112), fill="#4da3ff", width=4)
        draw.line((102, 94, 96, 112), fill="#4da3ff", width=4)
    elif kind == "snow":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((34, 98, 34, 110), fill="#ffffff", width=3)
        draw.line((34, 104, 34, 116), fill="#ffffff", width=3)
        draw.line((30, 102, 38, 102), fill="#ffffff", width=3)
        draw.line((78, 98, 78, 110), fill="#ffffff", width=3)
        draw.line((78, 104, 78, 116), fill="#ffffff", width=3)
        draw.line((74, 102, 82, 102), fill="#ffffff", width=3)
    elif kind == "snow_1flake":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((60, 98, 60, 114), fill="#ffffff", width=3)
        draw.line((54, 106, 66, 106), fill="#ffffff", width=3)
        draw.line((55, 101, 65, 111), fill="#ffffff", width=3)
        draw.line((65, 101, 55, 111), fill="#ffffff", width=3)
    elif kind == "snow_3flake":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        for x in (34, 60, 86):
            draw.line((x, 98, x, 114), fill="#ffffff", width=3)
            draw.line((x - 6, 106, x + 6, 106), fill="#ffffff", width=3)
            draw.line((x - 5, 101, x + 5, 111), fill="#ffffff", width=3)
            draw.line((x + 5, 101, x - 5, 111), fill="#ffffff", width=3)
    elif kind == "snow_6flake":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        for x, y in ((26, 98), (42, 98), (58, 98), (74, 98), (90, 98), (106, 98)):
            draw.line((x, y, x, y + 12), fill="#ffffff", width=2)
            draw.line((x - 4, y + 6, x + 4, y + 6), fill="#ffffff", width=2)
            draw.line((x - 3, y + 2, x + 3, y + 10), fill="#ffffff", width=2)
            draw.line((x + 3, y + 2, x - 3, y + 10), fill="#ffffff", width=2)
    elif kind == "sleet":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((28, 94, 24, 112), fill="#4da3ff", width=4)
        draw.line((52, 98, 52, 112), fill="#ffffff", width=3)
        draw.line((52, 104, 52, 116), fill="#ffffff", width=3)
        draw.line((48, 102, 56, 102), fill="#ffffff", width=3)
        draw.line((78, 94, 74, 112), fill="#4da3ff", width=4)
    elif kind == "storm":
        draw.ellipse((14, 44, 64, 94), fill="#d6dbe1")
        draw.ellipse((34, 26, 86, 76), fill="#d6dbe1")
        draw.ellipse((64, 44, 114, 94), fill="#d6dbe1")
        draw.rounded_rectangle((12, 54, 108, 96), radius=18, fill="#d6dbe1")
        draw.line((60, 56, 48, 76), fill="#ffd84d", width=7)
        draw.line((48, 76, 62, 76), fill="#ffd84d", width=7)
        draw.line((62, 76, 54, 96), fill="#ffd84d", width=7)
   
    image.save(path, format="GIF")


def ensure_background_asset():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    if BACKGROUND_IMAGE.exists():
        return

    image = Image.new("RGB", (760, 500), "#cdefff")
    draw = ImageDraw.Draw(image)

    draw.ellipse((580, 60, 690, 170), fill="#ffd84d")
    draw.rectangle((0, 300, 760, 500), fill="#8ed0f5")
    draw.rounded_rectangle((110, 170, 360, 255), radius=22, fill="#ffffff")
    draw.rounded_rectangle((230, 130, 490, 210), radius=22, fill="#ffffff")
    draw.rounded_rectangle((410, 170, 660, 255), radius=22, fill="#ffffff")
    draw.rounded_rectangle((150, 230, 420, 320), radius=22, fill="#ffffff")

    for left, top, right, bottom in [
        (90, 75, 210, 145),
        (150, 95, 250, 205),
        (88, 320, 150, 470),
        (95, 480, 150, 630),
    ]:
        draw.ellipse((left, top, right, bottom), fill="#ffffff")

    image.save(BACKGROUND_IMAGE, format="GIF")


def ensure_weather_icons():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for icon_name, icon_path in WEATHER_ICON_FILES.items():
        if not icon_path.exists():
            _create_icon_image(icon_path, icon_name)


class WeatherWindow:
    def __init__(self, root):
        ensure_background_asset()
        ensure_weather_icons()
        self.root = root
        self.root.title("Hava Durumu Uygulaması")
        self.root.geometry("840x660")
        self.root.resizable(False, False)

        self.background_image = tk.PhotoImage(file=str(BACKGROUND_IMAGE))
        self.background_label = tk.Label(self.root, image=self.background_image)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.card = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20)
        self.card.place(relx=0.5, rely=0.42, anchor="center", width=700, height=420)

        self.title = tk.Label(
            self.card,
            text="Hava Durumu",
            font=("Segoe UI", 20, "bold"),
            bg="#ffffff",
            fg="#1f2937",
        )
        self.title.pack(anchor="w")

        self.icon_images = {
            name: tk.PhotoImage(file=str(path)) for name, path in WEATHER_ICON_FILES.items()
        }
        self.icon_label = tk.Label(
            self.card,
            image=self.icon_images["sun"],
            bg="#ffffff",
        )
        self.icon_label.image = self.icon_images["sun"]
        self.icon_label.pack(anchor="w", pady=(6, 0))

        form_row = tk.Frame(self.card, bg="#ffffff")
        form_row.pack(fill="x", pady=(10, 8))

        tk.Label(form_row, text="Şehir: ", font=("Segoe UI", 11), bg="#ffffff").pack(side="left")
        self.city_entry = ttk.Entry(form_row, width=26)
        self.city_entry.insert(0, "Istanbul")
        self.city_entry.pack(side="left", padx=(6, 10))

        self.search_button = ttk.Button(form_row, text="Sorgula", command=self.search_weather)
        self.search_button.pack(side="left")

        self.location_var = tk.StringVar(value="--")
        self.temp_var = tk.StringVar(value="--")
        self.status_var = tk.StringVar(value="--")
        self.humidity_var = tk.StringVar(value="--")
        self.wind_var = tk.StringVar(value="--")

        info_frame = tk.Frame(self.card, bg="#ffffff")
        info_frame.pack(fill="x", pady=(12, 0))

        labels = [
            ("Konum", self.location_var),
            ("Sıcaklık", self.temp_var),
            ("Durum", self.status_var),
            ("Nem", self.humidity_var),
            ("Rüzgar", self.wind_var),
        ]

        for idx, (label_text, variable) in enumerate(labels):
            row = tk.Frame(info_frame, bg="#ffffff")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label_text}: ", font=("Segoe UI", 11, "bold"), bg="#ffffff").pack(side="left")
            tk.Label(row, textvariable=variable, font=("Segoe UI", 11), bg="#ffffff").pack(side="left")

        self.status_message = tk.Label(
            self.card,
            text="Canlı hava verisi Open-Meteo API'den gelir.",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#374151",
            justify="left",
        )
        self.status_message.pack(anchor="w", pady=(16, 0))

        self.forecast_title = tk.Label(
            self.card,
            text="5 Günlük Tahmin",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            justify="left",
        )
        self.forecast_title.pack(anchor="w", pady=(12, 4))

        self.forecast_var = tk.StringVar(value="-")
        self.forecast_label = tk.Label(
            self.card,
            textvariable=self.forecast_var,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#1f2937",
            justify="left",
            wraplength=650,
        )
        self.forecast_label.pack(anchor="w")

        self.root.after(50, self.search_weather)

    def search_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Uyarı", "Lütfen bir şehir adı girin.")
            return

        try:
            weather = get_current_weather(city)
            forecast_weather = get_forecast_weather(city)
            code = weather["weather_code"]
            icon_name = get_icon_name_for_code(code)
            self.location_var.set(f"{weather['city']}, {weather['country']}")
            self.temp_var.set(f"{weather['temperature']} °C")
            self.status_var.set(get_weather_description(code))
            self.humidity_var.set(f"{weather['humidity']} %")
            arrow = weather.get("wind_direction_arrow") or ""
            direction = weather.get("wind_direction_text") or ""
            wind_parts = [f"{weather['wind_speed']} km/s"]
            if arrow:
                wind_parts.append(arrow)
            if direction:
                wind_parts.append(direction)
            self.wind_var.set(" ".join(wind_parts))
            self.icon_label.configure(image=self.icon_images[icon_name])
            self.icon_label.image = self.icon_images[icon_name]
            self.forecast_var.set(format_forecast_lines(forecast_weather))
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))


def run_gui():
    root = tk.Tk()
    WeatherWindow(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
