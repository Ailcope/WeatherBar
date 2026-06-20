<div align="center" markdown="1">

# WeatherBar

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![macOS 12+](https://img.shields.io/badge/macOS-12+-000000?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![License: PolyForm NC](https://img.shields.io/badge/License-PolyForm%20NC-orange.svg?logo=opensourceinitiative&logoColor=white)](./LICENSE.md)

**Live weather in your macOS menu bar — pure Python, no Xcode.**
**La météo en direct dans votre barre de menu macOS — 100% Python, sans Xcode.**

Powered by **Open-Meteo** &bull; **Météo-France** &bull; **OpenWeatherMap**

[🇬🇧 English](#-english) &bull; [🇫🇷 Français](#-français)

</div>

---

<a id="-english"></a>

## 🇬🇧 English

### Overview

**WeatherBar** is a lightweight macOS menu bar app that shows live weather right where you can always see it — an emoji and the current temperature, next to your clock. Click it for a full breakdown: hourly forecast, daily highs and lows, sunrise and sunset, air quality, and one-click switching between your favorite cities. It runs entirely in Python — no Xcode, no app bundle, and no API key required.

### Features

- **Menu bar at a glance.** A weather emoji and the current temperature sit in your menu bar, refreshed automatically on an interval you control.
- **Full forecast.** Hourly outlook for the next few hours plus tomorrow's high/low, tucked into a tidy submenu.
- **Daily extremes & sun.** Today's min/max temperatures and the day's sunrise/sunset times.
- **Air quality.** European AQI with a color-coded rating, from the Open-Meteo Air Quality API.
- **GPS or favorites.** Auto-detect your location via CoreLocation, or pin favorite cities and switch in one click — add or remove them from the menu.
- **Pick your source.** Switch the forecast model — Météo-France (official FR), ECMWF, ICON, or auto — straight from the menu.
- **No key needed.** Works out of the box with free Open-Meteo; optionally plug in an OpenWeatherMap key.

### Install

```bash
pip3 install --user rumps requests pyobjc-framework-CoreLocation
python3 weather_menubar.py
```

### Usage

WeatherBar appears in your menu bar as a weather emoji and the temperature. Click it to:

- See details — feels-like, humidity, wind, air quality, today's min/max, sunrise/sunset
- Open **📅 Prévisions** for the hourly and next-day forecast
- Switch between favorite cities, or add / remove one
- Choose your weather **source** (forecast model)
- Toggle units (°C / °F) or set an OpenWeatherMap API key

### Configuration

Settings live in `~/.config/WeatherMenuBar/`:

- `config.json` — API key, units, refresh interval (`update_interval`, in seconds), and weather model
- `favorites.json` — your saved cities

Set `weather_model` in `config.json` (or pick it from the **🛰️ Source** menu):

| Value | Model |
|---|---|
| `"meteofrance_seamless"` | Météo-France AROME — default, best for France/Europe |
| `"ecmwf_ifs025"` | ECMWF — best global model |
| `"icon_seamless"` | ICON — Germany (DWD) |
| `""` | Open-Meteo best_match — auto by region |

Without a key, WeatherBar uses **Open-Meteo** (free, no signup) with the **Météo-France** model — the official French source and the closest match to Apple's Weather app for France. For OpenWeatherMap data, get a free key at [openweathermap.org](https://openweathermap.org/appid) and set it from the menu.

### License

[PolyForm Noncommercial 1.0.0](./LICENSE.md) — free to use, modify, and share for **noncommercial** purposes. Commercial use or reselling the code requires the author's permission.

---

<a id="-français"></a>

## 🇫🇷 Français

### Aperçu

**WeatherBar** est une app légère pour la barre de menu macOS qui affiche la météo en direct là où vous la voyez toujours — un emoji et la température actuelle, à côté de l'horloge. Cliquez dessus pour le détail complet : prévisions horaires, min/max du jour, lever et coucher du soleil, qualité de l'air, et changement de ville favorite en un clic. Tout tourne en Python — sans Xcode, sans bundle d'app, et sans clé API obligatoire.

### Fonctionnalités

- **Coup d'œil dans la barre de menu.** Un emoji météo et la température, actualisés automatiquement à l'intervalle de votre choix.
- **Prévisions complètes.** Les prochaines heures plus le min/max de demain, rangés dans un sous-menu propre.
- **Extrêmes & soleil.** Min/max du jour et heures de lever/coucher du soleil.
- **Qualité de l'air.** Indice européen (AQI) avec code couleur, via l'API Air Quality d'Open-Meteo.
- **GPS ou favoris.** Géolocalisation auto via CoreLocation, ou villes favorites épinglées — ajout/suppression depuis le menu.
- **Choisissez la source.** Changez de modèle — Météo-France (officiel FR), ECMWF, ICON, ou auto — directement depuis le menu.
- **Sans clé.** Fonctionne d'emblée avec Open-Meteo (gratuit) ; clé OpenWeatherMap optionnelle.

### Installation

```bash
pip3 install --user rumps requests pyobjc-framework-CoreLocation
python3 weather_menubar.py
```

### Utilisation

WeatherBar apparaît dans la barre de menu sous forme d'emoji météo + température. Cliquez pour :

- Voir les détails — ressenti, humidité, vent, qualité de l'air, min/max du jour, lever/coucher du soleil
- Ouvrir **📅 Prévisions** pour les prévisions horaires et de demain
- Changer de ville favorite, ou en ajouter / retirer une
- Choisir votre **source** météo (modèle)
- Basculer les unités (°C / °F) ou définir une clé API OpenWeatherMap

### Configuration

Les réglages sont dans `~/.config/WeatherMenuBar/` :

- `config.json` — clé API, unités, intervalle de rafraîchissement (`update_interval`, en secondes), modèle météo
- `favorites.json` — vos villes enregistrées

Définissez `weather_model` dans `config.json` (ou via le menu **🛰️ Source**) :

| Valeur | Modèle |
|---|---|
| `"meteofrance_seamless"` | Météo-France AROME — défaut, optimal en France/Europe |
| `"ecmwf_ifs025"` | ECMWF — meilleur modèle global |
| `"icon_seamless"` | ICON — Allemagne (DWD) |
| `""` | Open-Meteo best_match — auto par région |

Sans clé, WeatherBar utilise **Open-Meteo** (gratuit, sans inscription) avec le modèle **Météo-France** — la source officielle française et la plus proche de l'app Météo d'Apple. Pour les données OpenWeatherMap, créez une clé gratuite sur [openweathermap.org](https://openweathermap.org/appid) et renseignez-la depuis le menu.

### Licence

[PolyForm Noncommercial 1.0.0](./LICENSE.md) — libre d'utilisation, modification et partage à des fins **non commerciales**. Tout usage commercial ou revente du code nécessite l'accord de l'auteur.
