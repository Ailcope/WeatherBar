# ☀️ WeatherMenuBar

App menu bar macOS qui affiche la météo en live — 100% Python, sans Xcode.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![macOS](https://img.shields.io/badge/macOS-12%2B-000000)

## ✨ Fonctionnalités

- **🌡️ Météo en direct** dans la barre de menu (emoji + température)
- **📍 Géolocalisation GPS** automatique
- **⭐ Villes favorites** avec recherche et sélection rapide
- **🔄 Mise à jour automatique** toutes les 10 minutes
- **🌐 Fonctionne sans clé API** (Open-Meteo / modèle Météo-France officiel) ou avec OpenWeatherMap

## 🚀 Installation

```bash
# Installer les dépendances
pip3 install --user rumps requests pyobjc-framework-CoreLocation

# Lancer l'app
python3 weather_menubar.py
```

## 📱 Utilisation

L'app apparaît dans la barre de menu avec un emoji météo et la température.

Cliquez dessus pour voir :
- Détails météo (ressenti, humidité, vent)
- Favoris pour changer de ville
- Option d'ajouter de nouvelles villes

## ⚙️ Configuration

La configuration est stockée dans `~/.config/WeatherMenuBar/` :

- `config.json` — Clé API, unités, intervalle de mise à jour
- `favorites.json` — Liste des villes favorites

### Clé API (optionnel)

Sans clé API, l'app utilise **Open-Meteo** (gratuit, sans inscription) avec le
modèle **Météo-France** (AROME 1.3 km) — la source officielle pour la France,
la plus proche de l'app Météo d'Apple.

Pour changer de modèle, éditez `weather_model` dans `config.json` :
- `"meteofrance_seamless"` — Météo-France (défaut, optimal en France/Europe)
- `"ecmwf_ifs025"` — ECMWF, meilleur modèle global
- `""` — Open-Meteo best_match (auto-sélection par région)

Pour des données OpenWeatherMap, créez un compte gratuit sur [openweathermap.org](https://openweathermap.org/appid) et entrez votre clé via le menu.

## 🔧 Lancement automatique au démarrage

Pour lancer l'app automatiquement au démarrage du Mac :

1. Ouvrez **Préférences Système** → **Éléments d'ouverture**
2. Ajoutez un script ou utilisez un LaunchAgent (voir ci-dessous)

### Via LaunchAgent

```bash
# Créer le fichier LaunchAgent
cat > ~/Library/LaunchAgents/com.weathermenubar.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.weathermenubar</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>CHEMIN_VERS/weather_menubar.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Remplacez CHEMIN_VERS par le chemin réel
# Puis chargez-le :
launchctl load ~/Library/LaunchAgents/com.weathermenubar.plist
```
