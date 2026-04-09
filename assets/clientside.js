/* LILA – Client-side graph update  ·  Cyber-Tactical edition
 * Runs entirely in the browser: zero Python round-trip on slider drag.
 * All traces are scattergl (GPU/WebGL accelerated).
 */
window.dash_clientside = window.dash_clientside || {};

window.dash_clientside.lila = {

  updateGraph: function (sliderValue, matchStore, baseFig, entityFlags, heatmapFlags, heatmapMode) {

    // ── Guard: no data yet ───────────────────────────────────────────────────
    if (!matchStore || !baseFig) {
      return [baseFig || { data: [], layout: { template: 'plotly_dark' } }, "—", "—"];
    }

    const sv      = (sliderValue !== null && sliderValue !== undefined) ? Number(sliderValue) : 0;
    const sHumans = !entityFlags || entityFlags.includes('humans');
    const sBots   = !entityFlags || entityFlags.includes('bots');
    const sHeat   = Array.isArray(heatmapFlags) && heatmapFlags.includes('heatmap');
    const hMode   = heatmapMode || 'traffic';

    const rms   = matchStore.relative_ms;
    const px    = matchStore.pixel_x;
    const py    = matchStore.pixel_y;
    const ev    = matchStore.event;
    const uid   = matchStore.user_id;
    const isBot = matchStore.is_bot;
    const n     = rms.length;
    
    let eventsCurrent = 0;
    let playersKilled = 0;
    const totalPlayers = matchStore.total_players || 0;

    // ── Cyber-Tactical marker config ─────────────────────────────────────────
    //   Kill/BotKill  → cross,   Neon Red     (#ff4d4d)
    //   Loot          → diamond, Bright Gold  (#ffd700)
    //   Killed/BotKilled → x,   Deep Purple  (#bc13fe)
    //   KilledByStorm → x,      Hot Magenta  (#ff00c8)
    const MARKERS = {
      'Kill':          { symbol: 'cross',   color: '#ff4d4d', size: 13, name: 'Kill'        },
      'BotKill':       { symbol: 'cross',   color: '#ff4d4d', size: 13, name: 'Kill'        },
      'Loot':          { symbol: 'diamond', color: '#ffd700', size: 13, name: 'Loot'        },
      'Killed':        { symbol: 'x',       color: '#bc13fe', size: 13, name: 'Death'       },
      'BotKilled':     { symbol: 'x',       color: '#bc13fe', size: 13, name: 'Death'       },
      'KilledByStorm': { symbol: 'x',       color: '#ff00c8', size: 13, name: 'Storm Death' },
    };

    // ── Accumulate by user/event ─────────────────────────────────────────────
    const humanPaths  = {};   // userId → {x:[], y:[]}
    const botPaths    = {};
    const eventGroups = {};
    const heatX       = [];
    const heatY       = [];

    for (let i = 0; i < n; i++) {
      if (rms[i] > sv) continue;   // ← CORE TIME FILTER
      eventsCurrent++;

      const bot   = isBot[i];
      const event = ev[i];
      const x     = px[i];
      const y     = py[i];
      const u     = uid[i];

      if ((event === 'Killed' || event === 'KilledByStorm') && !bot) {
        playersKilled++;
      }

      if (event === 'Position' && sHumans && !bot) {
        if (!humanPaths[u]) humanPaths[u] = { x: [], y: [] };
        humanPaths[u].x.push(x);
        humanPaths[u].y.push(y);
      } else if (event === 'BotPosition' && sBots && bot) {
        if (!botPaths[u]) botPaths[u] = { x: [], y: [] };
        botPaths[u].x.push(x);
        botPaths[u].y.push(y);
      }

      if (MARKERS[event]) {
        const show = (!bot && sHumans) || (bot && sBots);
        if (show) {
          if (!eventGroups[event]) eventGroups[event] = { x: [], y: [], text: [] };
          eventGroups[event].x.push(x);
          eventGroups[event].y.push(y);
          
          let mins = Math.floor(rms[i] / 60000);
          let secs = Math.floor((rms[i] % 60000) / 1000);
          let eStr = bot ? "Bot" : "Human";
          eventGroups[event].text.push(`${MARKERS[event].name} | Timestamp: ${mins}m ${secs}s | Entity: ${eStr}`);
        }
      }

      if (sHeat) {
        const isHeatPos   = hMode === 'traffic' && (event === 'Position' || event === 'BotPosition');
        const isHeatDeath = hMode === 'death'   && (event === 'Killed'   || event === 'KilledByStorm');
        if (isHeatPos || isHeatDeath) {
          if ((!bot && sHumans) || (bot && sBots)) {
            heatX.push(x);
            heatY.push(y);
          }
        }
      }
    }

    // ── Build traces ─────────────────────────────────────────────────────────
    const traces = [];

    // ── Heatmap: organic neon-to-transparent glow ─────────────────────────
    if (sHeat && heatX.length > 1) {
      // Custom colorscale: transparent black → deep indigo → cyan → white
      const neonScale = [
        [0.00, 'rgba(0,0,0,0)'],
        [0.20, 'rgba(10,0,80,0.4)'],
        [0.45, 'rgba(0,50,180,0.65)'],
        [0.70, 'rgba(0,180,255,0.85)'],
        [1.00, 'rgba(200,240,255,1)'],
      ];
      traces.push({
        type:        'histogram2dcontour',
        x:           heatX,
        y:           heatY,
        colorscale:  neonScale,
        reversescale: false,
        opacity:     0.55,
        ncontours:   20,
        contours:    { coloring: 'heatmap', showlines: false },
        line:        { width: 0 },
        showscale:   false,
        name:        'Heatmap',
        hovertemplate: 'Density<extra></extra>',
        // Clamp to avoid washing out at sparse regions
        zauto:       true,
      });
    }

    // ── Human paths — neon cyan GLOW (two-pass)  ─────────────────────────
    //   Pass 1: wide, low-opacity glow halo
    //   Pass 2: sharp inner line at full brightness
    for (const [, path] of Object.entries(humanPaths)) {
      if (path.x.length < 2) continue;
      // Outer glow
      traces.push({
        type:      'scattergl',
        x:         path.x,
        y:         path.y,
        mode:      'lines',
        line:      { color: '#00f2ff', width: 9 },
        opacity:   0.12,
        hoverinfo: 'skip',
        showlegend: false,
      });
      // Inner sharp line
      traces.push({
        type:      'scattergl',
        x:         path.x,
        y:         path.y,
        mode:      'lines',
        line:      { color: '#00f2ff', width: 2.5 },
        opacity:   0.85,
        hoverinfo: 'skip',
        showlegend: false,
      });
    }

    // ── Bot paths — dashed light grey ─────────────────────────────────────
    for (const [, path] of Object.entries(botPaths)) {
      if (path.x.length < 2) continue;
      traces.push({
        type:      'scattergl',
        x:         path.x,
        y:         path.y,
        mode:      'lines',
        line:      { color: '#aebbc2', width: 2, dash: 'dot' },
        opacity:   0.55,
        hoverinfo: 'skip',
        showlegend: false,
      });
    }

    // ── Event markers — rendered LAST so they sit on top ─────────────────
    for (const [eventName, pts] of Object.entries(eventGroups)) {
      const m = MARKERS[eventName];
      traces.push({
        type:    'scattergl',
        x:       pts.x,
        y:       pts.y,
        text:    pts.text,
        hovertemplate: '%{text}<extra></extra>',
        mode:    'markers',
        marker:  {
          symbol: m.symbol,
          color:  m.color,
          size:   m.size,
          line:   { color: 'rgba(0,0,0,0.7)', width: 1.5 },
        },
        opacity: 1.0,
        name:    m.name,
      });
    }

    let survivalRateStr = "—";
    if (totalPlayers > 0) {
      let alive = Math.max(0, totalPlayers - playersKilled);
      survivalRateStr = ((alive / totalPlayers) * 100).toFixed(1) + "%";
    }

    // ── Return figure with updated traces on the pre-built layout ─────────
    return [{ data: traces, layout: baseFig.layout }, String(eventsCurrent), survivalRateStr];
  }

};
