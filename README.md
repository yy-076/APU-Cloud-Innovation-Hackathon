# 🌱 EcoSprout

**An AI-powered smart facility and energy platform for the APU campus.**

EcoSprout monitors IoT sensor data across campus rooms, flags energy waste, and uses Google Gemini to explain problems and write energy-saving action plans. It also estimates the money and carbon a campus could save.

Built by **Team Mushroom 🍄** for the APU Hackathon.

<!-- Add your team members here, e.g. - Name — Role -->

| Light mode | Dark mode |
| --- | --- |
| ![EcoSprout in light mode](screenshots/light.png) | ![EcoSprout in dark mode](screenshots/dark.png) |

---

## ✨ Features

The app has six modules, which you open from the sidebar:

| Module | What it does |
| --- | --- |
| 🏢 **Campus-Wide Analytics Overview** | Summary table and power-draw chart for the auditoriums and Blocks A–E |
| 📊 **Live Zone Telemetry & 24h Trends** | Occupancy, room temperature, AC status and connected Wi-Fi devices for any of 42 zones, plus a 24-hour power and temperature chart |
| 🚨 **Anomaly Detection & AI Triage** | Scores each zone for energy waste and asks Gemini to explain the root cause. Demo mode simulates a high-waste scenario |
| 🤖 **Gemini AI Audit & PDF Reports** | Gemini writes an energy optimisation plan for the selected zone, which you can download as a PDF report |
| 🎛️ **Live IoT Actuator Controls** | Buttons for Eco-Mode, deep sleep and fresh-air flushing (simulated commands) |
| 🌱 **Sustainability & Cost ROI** | Daily kWh, cost in RM and CO₂ for a zone, with a slider that projects savings across up to 50 zones |

The app also has a light and dark theme, and it shows friendly messages when Gemini is busy or the API key is wrong.

### How the anomaly score works

| Rule | Points |
| --- | --- |
| AC is **ON** with 5 or fewer people in the room | +45 |
| Wi-Fi devices exceed `occupancy × 3 + 20` (idle devices drawing power) | +35 |
| Room temperature below 21 °C (over-cooling) | +20 |

A score **above 40** is flagged as high energy waste, **1–40** as a moderate inefficiency, and **0** as running efficiently.

### Assumptions used in the calculations

- Electricity tariff: **RM 0.50 per kWh**
- Carbon factor: **0.58 kg CO₂ per kWh**
- Rooms run **12 hours a day**
- Estimated power: **12.5 kW** with AC on, **8 kW** in Eco or Auto mode
- Savings: **25%** per zone with AI Eco-Mode, and **30%** for the campus-wide projection

---

## 🛠️ Tech stack

- [Streamlit](https://streamlit.io/) for the web interface
- [Google Gemini](https://ai.google.dev/) (`gemini-3.8-flash`) through the `google-genai` SDK
- pandas and NumPy for data and charts
- fpdf2 for PDF reports

---

## 🚀 Getting started

### What you need

- Python 3.10 or newer
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Install and run

```bash
git clone <this-repo-url>
cd apu-hackathon-energy-saver

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>. Paste your Gemini API key into the box in the sidebar to use the AI features. The key is only kept for your current session and is never saved to a file.

---

## 📁 Project structure

```
apu-hackathon-energy-saver/
├── .streamlit/
│   └── config.toml      # light and dark theme colours
├── screenshots/         # images used in this README
├── app.py               # the whole app
├── requirements.txt
└── README.md
```

---

## ⚠️ Notes

- **Sensor data is simulated.** Each zone gets random readings the first time you open it, and they stay the same for the rest of your session. The app isn't connected to real sensors yet.
- **Actuator controls are a demo.** The buttons show a confirmation but don't control real hardware.
- **Gemini can be busy.** On the free tier, Gemini sometimes returns a "high demand" error. Wait a moment and try again.

---

## 🍄 Team Mushroom

Made with 🍄 by Team Mushroom for the APU Hackathon.
Powered by Google Cloud & Gemini.
