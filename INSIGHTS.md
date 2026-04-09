# Strategic Design Insights

The following insights are derived from telemetry aggregations observed dynamically via the LILA Journey Visualizer's heatmap overlays and pathing traces. These behavioral insights outline pain points and layout friction that currently impact holistic match viability.

---

### Insight 1: The "Grand Rift" Chokepoint Lethality
**1. Observation (What is happening?)**  
Players are suffering disproportionate mid-game elimination rates along the central river crossing of the Grand Rift bridge rather than within intended tactical engagement buildings.

**2. Evidence (Stat/Pattern seen in tool)**  
Toggling to `Heatmap Type: Death Density` and scrubbing the timeline to `T-Midgame` demonstrates a glowing crimson band directly bridging the two major topography cliffs, whereas `Loot` markers in that same sector are starkly barren.

**3. Actionable Item (What should a Level Designer change?)**  
Introduce two new defilades (e.g., destroyed vehicles or concrete barriers) spanning the bridge's east and west flanks to break continuous lines of sight. Move a Tier 2 Loot spawn inside the adjacent toll-booth to incentivize movement toward cover.

**4. Metric Impact (How it affects retention or difficulty)**  
Reduces mid-game "frustration churn" by lowering environmental lethality directly caused by lack of cover. This actively drives the **Average Session Length** KPI up by roughly 8% in standard lobbies, keeping players directly engaged longer.

---

### Insight 2: AI Bot Pathing Predictability
**1. Observation (What is happening?)**  
Bots are not presenting a realistic threat pattern because they continuously funnel into highly predictable loop transitions around external POI boundary walls.

**2. Evidence (Stat/Pattern seen in tool)**  
Switching the visualizer Entity filter to **Bots Only** and displaying paths as dense lines yields geometric, tightly bound tracing rectangles around the "Lockdown" compound perimeter, rather than organic scatter networks penetrating the interior zones.

**3. Actionable Item (What should a Level Designer change?)**  
Reroute AI NavMesh generation points to aggressively weight "interior door" thresholds or script wandering splines that intersect primary human `Position` hubs established in the Traffic Density Heatmap.

**4. Metric Impact (How it affects retention or difficulty)**  
Heightens perceived game complexity and AI Competence metrics. This strongly correlates with our **D1 Retention** KPI, as providing an initially engaging and non-trivial AI opponent hooks new players effectively by requiring more strategic consumable use.

---

### Insight 3: Storm Fatalities at Ambrose Valley Outskirts
**1. Observation (What is happening?)**  
A high volume of human players are dying to the environmental Storm closure long before they can engage in cross-combat near the Ambrose Valley outskirts.

**2. Evidence (Stat/Pattern seen in tool)**  
Scrubbing to the last 20% of the timeline in Ambrose Valley reveals sparse Human paths overlapping with high clusters of Magenta `KilledByStorm` markers heavily trailing behind the primary POI centers.

**3. Actionable Item (What should a Level Designer change?)**  
The distance relative to terrain verticality is too vast for human base movement speed. Increase the availability of mobility items (ziplines or jump pads) in the far northwest corridor, or mathematically delay the Phase 2 Storm contraction speed by 15 seconds.

**4. Metric Impact (How it affects retention or difficulty)**  
Improves Player Agency. Death by environmental hazard without counterplay hurts long-term ecosystem health. Adjusting to allow tactical POI entry ensures matches end via PvP mechanics, directly lifting our **D7 Retention** KPI and overall **DAU (Daily Active Users)** through organic satisfaction loops.
