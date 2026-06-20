#!/usr/bin/env python3
"""
WeatherMenuBar — Live weather in your macOS menu bar.
Features:
  • Live weather display (emoji + temp) in the menu bar
  • Auto-detect location via GPS (CoreLocation)
  • Favorite cities with quick switching
  • OpenWeatherMap API integration
"""

import json
import os
import threading
import time
from pathlib import Path

import requests
import rumps

# Hide Python icon from Dock (must be before any AppKit window is created)
try:
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )
except Exception:
    pass  # AppKit not available, ignore

# ─── Configuration ──────────────────────────────────────────────────────────────

CONFIG_DIR = Path.home() / ".config" / "WeatherMenuBar"
CONFIG_FILE = CONFIG_DIR / "config.json"
FAVORITES_FILE = CONFIG_DIR / "favorites.json"

DEFAULT_CONFIG = {
    "api_key": "",  # OpenWeatherMap API key
    "units": "metric",  # metric / imperial
    "update_interval": 600,  # seconds (10 min)
    "current_city": None,  # None = auto GPS
    "language": "fr",
    # Open-Meteo model. "meteofrance_seamless" = Météo-France AROME (1.3km,
    # autorité officielle FR) + ARPEGE global en fallback hors zone haute-réso.
    # Empty string "" = Open-Meteo best_match (auto-sélection par région).
    "weather_model": "meteofrance_seamless",
}

WEATHER_EMOJIS = {
    "01d": "☀️", "01n": "🌙",
    "02d": "⛅", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
}

UNIT_SYMBOLS = {"metric": "°C", "imperial": "°F"}


# ─── Helpers ─────────────────────────────────────────────────────────────────────

def ensure_config():
    """Create config directory and default files if they don't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False))
    if not FAVORITES_FILE.exists():
        default_favs = [
            {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
            {"name": "Lyon", "lat": 45.7640, "lon": 4.8357},
            {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        ]
        FAVORITES_FILE.write_text(json.dumps(default_favs, indent=2, ensure_ascii=False))


def load_config():
    ensure_config()
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    # Merge with defaults for any missing keys
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
    return cfg


def save_config(cfg):
    ensure_config()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_favorites():
    ensure_config()
    with open(FAVORITES_FILE) as f:
        return json.load(f)


def save_favorites(favs):
    ensure_config()
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favs, f, indent=2, ensure_ascii=False)


# ─── CoreLocation delegate (defined once at module level to avoid ObjC class conflict)
_LocationDelegate = None
try:
    from CoreLocation import CLLocationManager, kCLLocationAccuracyHundredMeters
    from Foundation import NSRunLoop, NSDate, NSObject
    import objc

    class WeatherMenuBarLocationDelegate(NSObject):
        """CoreLocation delegate — receives GPS updates."""
        lat = objc.ivar('lat')
        lon = objc.ivar('lon')
        done = objc.ivar.bool('done')

        def init(self):
            self = objc.super(WeatherMenuBarLocationDelegate, self).init()
            if self is not None:
                self.lat = None
                self.lon = None
                self.done = False
            return self

        def locationManager_didUpdateLocations_(self, manager, locations):
            if locations and len(locations) > 0:
                loc = locations[-1]
                coord = loc.coordinate()
                self.lat = coord.latitude
                self.lon = coord.longitude
                self.done = True
                manager.stopUpdatingLocation()

        def locationManager_didFailWithError_(self, manager, error):
            print(f"[GPS] Erreur CoreLocation: {error.localizedDescription()}")
            self.done = True

    _LocationDelegate = WeatherMenuBarLocationDelegate
except Exception as _e:
    print(f"[GPS] CoreLocation non disponible: {_e}")


def get_gps_location():
    """Get current GPS coordinates using macOS CoreLocation."""
    if _LocationDelegate is not None:
        try:
            manager = CLLocationManager.alloc().init()
            delegate = _LocationDelegate.alloc().init()
            manager.setDelegate_(delegate)
            manager.setDesiredAccuracy_(kCLLocationAccuracyHundredMeters)
            manager.startUpdatingLocation()

            # Wait up to 10 seconds
            for _ in range(20):
                NSRunLoop.currentRunLoop().runUntilDate_(
                    NSDate.dateWithTimeIntervalSinceNow_(0.5)
                )
                if delegate.done:
                    break

            if delegate.lat is not None:
                return delegate.lat, delegate.lon
        except Exception as e:
            print(f"[GPS] Erreur CoreLocation: {e}")

    # Fallback: IP-based geolocation
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        data = r.json()
        loc = data.get("loc", "48.8566,2.3522")
        lat, lon = loc.split(",")
        return float(lat), float(lon)
    except Exception:
        return 48.8566, 2.3522  # Default: Paris


def fetch_weather(lat, lon, api_key, units="metric", lang="fr", model="meteofrance_seamless"):
    """Fetch weather. Open-Meteo (Météo-France model) by default; OpenWeatherMap if a key is set."""
    if not api_key:
        # Open-Meteo — free, no key. Default model = Météo-France (officiel FR).
        return fetch_weather_open_meteo(lat, lon, units, model)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units,
        "lang": lang,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        icon = data["weather"][0].get("icon", "01d")
        return {
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"].capitalize(),
            "icon": icon,
            "emoji": WEATHER_EMOJIS.get(icon, "🌡️"),
            "city": data.get("name", "?"),
            "wind_speed": round(data.get("wind", {}).get("speed", 0) * 3.6, 1),  # m/s → km/h
        }
    except Exception as e:
        print(f"[Weather] OpenWeatherMap error: {e}")
        return fetch_weather_open_meteo(lat, lon, units, model)


def fetch_weather_open_meteo(lat, lon, units="metric", model="meteofrance_seamless"):
    """Open-Meteo weather — free, no key. `model` picks the forecast model (empty = best_match)."""
    temp_unit = "celsius" if units == "metric" else "fahrenheit"
    wind_unit = "kmh" if units == "metric" else "mph"
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
        "temperature_unit": temp_unit,
        "wind_speed_unit": wind_unit,
        "timezone": "auto",
    }
    if model:
        params["models"] = model
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data["current"]
        wmo = current.get("weather_code", 0)
        emoji = wmo_to_emoji(wmo)

        # Reverse geocode for city name
        city = reverse_geocode(lat, lon)

        return {
            "temp": round(current["temperature_2m"]),
            "feels_like": round(current["apparent_temperature"]),
            "humidity": round(current["relative_humidity_2m"]),
            "description": wmo_description(wmo),
            "icon": "01d",
            "emoji": emoji,
            "city": city,
            "wind_speed": round(current["wind_speed_10m"], 1),
        }
    except Exception as e:
        print(f"[Weather] Open-Meteo error: {e}")
        return None


def reverse_geocode(lat, lon):
    """Get city name from coordinates using Open-Meteo geocoding."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10}
        headers = {"User-Agent": "WeatherMenuBar/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=5)
        data = r.json()
        addr = data.get("address", {})
        return addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or "?"
    except Exception:
        return "?"


def wmo_to_emoji(code):
    """Convert WMO weather code to emoji."""
    if code == 0:
        return "☀️"
    elif code in (1, 2, 3):
        return "⛅"
    elif code in (45, 48):
        return "🌫️"
    elif code in (51, 53, 55, 56, 57):
        return "🌦️"
    elif code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "🌧️"
    elif code in (71, 73, 75, 77, 85, 86):
        return "❄️"
    elif code in (95, 96, 99):
        return "⛈️"
    return "🌡️"


def wmo_description(code):
    """Convert WMO weather code to French description."""
    descriptions = {
        0: "Ciel dégagé",
        1: "Principalement dégagé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine légère",
        53: "Bruine modérée",
        55: "Bruine dense",
        56: "Bruine verglaçante légère",
        57: "Bruine verglaçante dense",
        61: "Pluie légère",
        63: "Pluie modérée",
        65: "Pluie forte",
        66: "Pluie verglaçante légère",
        67: "Pluie verglaçante forte",
        71: "Neige légère",
        73: "Neige modérée",
        75: "Neige forte",
        77: "Grains de neige",
        80: "Averses légères",
        81: "Averses modérées",
        82: "Averses violentes",
        85: "Averses de neige légères",
        86: "Averses de neige fortes",
        95: "Orage",
        96: "Orage avec grêle légère",
        99: "Orage avec grêle forte",
    }
    return descriptions.get(code, f"Code météo {code}")


def search_city(query):
    """Search for a city using Open-Meteo geocoding API."""
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query, "count": 5, "language": "fr"}
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        return [
            {
                "name": f"{r['name']}, {r.get('country', '')}",
                "lat": r["latitude"],
                "lon": r["longitude"],
            }
            for r in results
        ]
    except Exception as e:
        print(f"[Search] Error: {e}")
        return []


# ─── Menu Bar App ────────────────────────────────────────────────────────────────

class WeatherMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("🌡️ --°", quit_button=None)

        self.config = load_config()
        self.favorites = load_favorites()
        self.weather_data = None
        self.current_lat = None
        self.current_lon = None

        # Build menu
        self._build_menu()

        # Initial weather fetch in background
        self._refresh_weather_async()

    def _build_menu(self):
        """Build the dropdown menu."""
        self.menu.clear()

        # ── Weather details section
        self.menu_details = rumps.MenuItem("⏳ Chargement…")
        self.menu_details.set_callback(None)
        self.menu.add(self.menu_details)

        self.menu_feels = rumps.MenuItem("")
        self.menu_feels.set_callback(None)
        self.menu.add(self.menu_feels)

        self.menu_humidity = rumps.MenuItem("")
        self.menu_humidity.set_callback(None)
        self.menu.add(self.menu_humidity)

        self.menu_wind = rumps.MenuItem("")
        self.menu_wind.set_callback(None)
        self.menu.add(self.menu_wind)

        self.menu.add(rumps.separator)

        # ── Location section
        self.menu_gps = rumps.MenuItem("📍 Ma position (GPS)")
        self.menu.add(self.menu_gps)

        self.menu.add(rumps.separator)

        # ── Favorites section
        self.menu_fav_title = rumps.MenuItem("⭐ Favoris")
        self.menu_fav_title.set_callback(None)
        self.menu.add(self.menu_fav_title)

        self._rebuild_favorites_menu()

        self.menu.add(rumps.separator)

        # ── Add / Search city
        self.menu_add_city = rumps.MenuItem("➕ Ajouter une ville…")
        self.menu.add(self.menu_add_city)

        self.menu.add(rumps.separator)

        # ── Settings
        self.menu_api_key = rumps.MenuItem("🔑 Configurer clé API")
        self.menu.add(self.menu_api_key)

        self.menu_units = rumps.MenuItem(
            "🌡️ Unités: " + ("°C (Métrique)" if self.config["units"] == "metric" else "°F (Impérial)")
        )
        self.menu.add(self.menu_units)

        self.menu.add(rumps.separator)

        # ── Refresh / Quit
        self.menu_refresh = rumps.MenuItem("🔄 Actualiser maintenant")
        self.menu.add(self.menu_refresh)

        self.menu_quit = rumps.MenuItem("❌ Quitter")
        self.menu.add(self.menu_quit)

    def _rebuild_favorites_menu(self):
        """Rebuild the favorites submenu items."""
        # Remove old favorite items
        keys_to_remove = [k for k in self.menu.keys() if isinstance(k, str) and k.startswith("  ★")]
        for k in keys_to_remove:
            del self.menu[k]

        # Add current favorites after the title
        for i, fav in enumerate(self.favorites):
            key = f"  ★ {fav['name']}"
            item = rumps.MenuItem(key)
            item.set_callback(lambda sender, f=fav: self._select_favorite(f))
            # Insert after the favorites title
            self.menu.insert_after(self.menu_fav_title.title, item)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    @rumps.clicked("📍 Ma position (GPS)")
    def on_gps(self, _):
        """Switch to GPS auto-location."""
        self.config["current_city"] = None
        save_config(self.config)
        rumps.notification("WeatherMenuBar", "", "📍 Position GPS activée")
        self._refresh_weather_async()

    @rumps.clicked("➕ Ajouter une ville…")
    def on_add_city(self, _):
        """Add a new city to favorites via search."""
        window = rumps.Window(
            message="Entrez le nom d'une ville à rechercher :",
            title="Ajouter une ville",
            default_text="",
            ok="Rechercher",
            cancel="Annuler",
            dimensions=(300, 24),
        )
        response = window.run()
        if response.clicked and response.text.strip():
            query = response.text.strip()
            results = search_city(query)
            if not results:
                rumps.alert("Aucune ville trouvée", f"Pas de résultat pour « {query} »")
                return

            # Show results as a selection
            msg = "Résultats :\n\n"
            for i, r in enumerate(results, 1):
                msg += f"  {i}. {r['name']}\n"
            msg += "\nEntrez le numéro de votre choix :"

            win2 = rumps.Window(
                message=msg,
                title="Sélectionner une ville",
                default_text="1",
                ok="Ajouter aux favoris",
                cancel="Annuler",
                dimensions=(300, 24),
            )
            resp2 = win2.run()
            if resp2.clicked:
                try:
                    idx = int(resp2.text.strip()) - 1
                    if 0 <= idx < len(results):
                        city = results[idx]
                        # Check if already in favorites
                        if not any(f["name"] == city["name"] for f in self.favorites):
                            self.favorites.append(city)
                            save_favorites(self.favorites)
                            self._rebuild_favorites_menu()
                            rumps.notification(
                                "WeatherMenuBar", "",
                                f"⭐ {city['name']} ajouté aux favoris"
                            )
                        else:
                            rumps.alert("Déjà en favoris", f"{city['name']} est déjà dans vos favoris.")

                        # Switch to this city
                        self._select_favorite(city)
                except (ValueError, IndexError):
                    rumps.alert("Erreur", "Numéro invalide.")

    @rumps.clicked("🔑 Configurer clé API")
    def on_api_key(self, _):
        """Set or update the OpenWeatherMap API key."""
        current = self.config.get("api_key", "")
        msg = "Entrez votre clé API OpenWeatherMap :\n(gratuite sur openweathermap.org)\n"
        if not current:
            msg += "\n💡 Sans clé, l'app utilise Open-Meteo (gratuit, sans inscription)."
        else:
            msg += f"\n✅ Clé actuelle : {current[:8]}…"

        window = rumps.Window(
            message=msg,
            title="Clé API OpenWeatherMap",
            default_text=current,
            ok="Enregistrer",
            cancel="Annuler",
            dimensions=(400, 24),
        )
        response = window.run()
        if response.clicked:
            self.config["api_key"] = response.text.strip()
            save_config(self.config)
            rumps.notification("WeatherMenuBar", "", "🔑 Clé API enregistrée !")
            self._refresh_weather_async()

    @rumps.clicked("🌡️ Unités: °C (Métrique)")
    @rumps.clicked("🌡️ Unités: °F (Impérial)")
    def on_toggle_units(self, sender):
        """Toggle between metric and imperial units."""
        if self.config["units"] == "metric":
            self.config["units"] = "imperial"
        else:
            self.config["units"] = "metric"
        save_config(self.config)
        label = "°C (Métrique)" if self.config["units"] == "metric" else "°F (Impérial)"
        sender.title = f"🌡️ Unités: {label}"
        self._refresh_weather_async()

    @rumps.clicked("🔄 Actualiser maintenant")
    def on_refresh(self, _):
        """Manual refresh."""
        self.title = "🔄 …"
        self._refresh_weather_async()

    @rumps.clicked("❌ Quitter")
    def on_quit(self, _):
        rumps.quit_application()

    def _select_favorite(self, fav):
        """Switch to a favorite city."""
        self.config["current_city"] = fav
        save_config(self.config)
        rumps.notification("WeatherMenuBar", "", f"📍 Ville : {fav['name']}")
        self._refresh_weather_async()

    # ── Timer for periodic refresh ────────────────────────────────────────────

    @rumps.timer(600)  # Every 10 minutes
    def auto_refresh(self, _):
        self._refresh_weather_async()

    # ── Background weather fetch ──────────────────────────────────────────────

    def _refresh_weather_async(self):
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        try:
            # Determine location
            city_cfg = self.config.get("current_city")
            if city_cfg and "lat" in city_cfg:
                lat, lon = city_cfg["lat"], city_cfg["lon"]
            else:
                lat, lon = get_gps_location()
                self.current_lat = lat
                self.current_lon = lon

            # Fetch weather
            data = fetch_weather(
                lat, lon,
                self.config.get("api_key", ""),
                self.config.get("units", "metric"),
                self.config.get("language", "fr"),
                self.config.get("weather_model", "meteofrance_seamless"),
            )

            if data:
                self.weather_data = data
                unit = UNIT_SYMBOLS.get(self.config["units"], "°C")
                wind_unit = "km/h" if self.config["units"] == "metric" else "mph"

                # Update menu bar title
                self.title = f"{data['emoji']} {data['temp']}{unit}"

                # Update dropdown details
                self.menu_details.title = f"📍 {data['city']} — {data['description']}"
                self.menu_feels.title = f"🌡️ Ressenti : {data['feels_like']}{unit}"
                self.menu_humidity.title = f"💧 Humidité : {data['humidity']}%"
                self.menu_wind.title = f"💨 Vent : {data['wind_speed']} {wind_unit}"
            else:
                self.title = "⚠️ Erreur"
                self.menu_details.title = "❌ Impossible de charger la météo"
        except Exception as e:
            print(f"[Refresh] Error: {e}")
            self.title = "⚠️ ?"


# ─── Entry point ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ensure_config()
    app = WeatherMenuBarApp()
    app.run()
