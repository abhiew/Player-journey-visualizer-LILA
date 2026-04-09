# LILA Player Journey Visualizer

![LILA Journey Visualizer Screenshot](https://via.placeholder.com/1200x600/0b0d10/00f2ff?text=LILA+Tactical+Dashboard)

*A high-performance, WebGL-accelerated tactical visualization dashboard built for analyzing player and bot behavior within LILA Games.*

**Hosted URL Placeholder**: [Deploy to Dash Enterprise / AWS / Heroku]

---

## 🎯 Core Features

The Visualizer transforms raw telemetry data (Parquet) into actionable, granular insights via a "Cyber-Tactical" Night Mode interface.

- [x] **Zero-Latency Playback**: Fully client-side processing using JS callbacks for 60FPS scrubbing across millisecond-scale telemetry.
- [x] **Entity Distinction**: Instantly differentiate humans (Neon Cyan solid traces) from AI Bots (Dashed Grey traces) running on an inverted UUID classification logic.
- [x] **WebGL Accelerated**: Renders 10,000+ data points smoothly in the browser via `Plotly ScatterGL`.
- [x] **Interactive Heatmaps**: Density overlays for mapping popular traffic corridors and lethality zones (Kill/Death clusters).
- [x] **Granular Event Markers**: Distinct symbology for Kills (Cross), Looting (Diamond), Deaths (X), and Storm Deaths (Magenta X).
- [x] **Responsive AAA UI**: Strict flexbox layout pinned to a `100vh` non-scrolling viewport, adhering to premium deep-dark aesthetic standards.

---

## 🛠 Setup & Installation

### Requirements
- Python 3.10+
- Pip / Virtual environment

### 1. Clone the Repository
```bash
git clone https://github.com/LilaGames/journey-visualizer.git
cd journey-visualizer
```

### 2. Environment Setup
We recommend using a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Provide Data
Ensure your telemetry `.parquet` files and `minimaps` directory are placed within the `player_data/` root folder. The directory should mirror this structure:
```text
player_data/
├── minimaps/
│   ├── AmbroseValley_Minimap.png
│   └── ...
└── February_14/
    └── 1000_UUID.nakama-0.parquet
```

### 5. Launch the Dashboard
Run the Dash server locally:
```bash
python app.py
```
Open your browser to [http://localhost:8050](http://localhost:8050)

---

## 🏗 Architecture & Insights
For deep dives into coordinate mapping math, application state management, and product thinking, please refer to our internal documentation:
- [System Architecture](ARCHITECTURE.md)
- [Product Insights Template](INSIGHTS.md)

---

## 🚀 Future Roadmap

We are actively exploring the following "Pro" features for upcoming iterations:

- **3D Pathing Visualization:** Transitioning to a fully 3D interactive camera context to analyze player verticality during base defense and high-ground combat.
- **Squad-Based Grouping:** Implementing dynamic grouping polygons to visualize team dispersion, identifying whether tightly clustered or widely split squads have higher survival duration.
