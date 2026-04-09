from __future__ import annotations

import base64
from pathlib import Path

import dash
from dash import ClientsideFunction, Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from data_manager import DataManager, get_map_image_path, get_pixel_coords


def _to_data_uri(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = (Path(__file__).resolve().parent / p).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Minimap not found: {p}")
    ext = p.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    encoded = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


# Encode each minimap once per process (not on every slider tick).
_MAP_IMAGE_URI_CACHE: dict[str, str] = {}


def _get_map_image_uri(map_id: str) -> str:
    if map_id not in _MAP_IMAGE_URI_CACHE:
        _MAP_IMAGE_URI_CACHE[map_id] = _to_data_uri(get_map_image_path(map_id))
    return _MAP_IMAGE_URI_CACHE[map_id]






def _load_data() -> pd.DataFrame:
    dm = DataManager("player_data")
    df = dm.load_all_data()
    if df.empty:
        return df

    out = df.copy()
    out["map_id"] = out["map_id"].astype("string")
    out["date"] = out["date"].astype("string")
    out["match_id"] = out["match_id"].astype("string")
    out["user_id"] = out["user_id"].astype("string")
    out["event"] = out["event"].astype("string")

    out["ts"] = pd.to_datetime(out["ts"], errors="coerce")
    out = out.dropna(subset=["ts", "x", "z", "map_id", "match_id", "date"])

    # datetime64[ms] cast to int64 gives epoch-milliseconds directly.
    out["ts_ms"] = out["ts"].astype("int64")

    # relative_ms: milliseconds from the first event in each match, zero-based.
    # Diagnostics confirm each match spans ~50–900 ms of real event data.
    match_key = ["map_id", "date", "match_id"]
    out["relative_ms"] = (
        out["ts_ms"] - out.groupby(match_key, sort=False)["ts_ms"].transform("min")
    ).astype(np.int64)

    out = out.sort_values(match_key + ["relative_ms"]).reset_index(drop=True)

    pixels = out.apply(
        lambda row: get_pixel_coords(float(row["x"]), float(row["z"]), str(row["map_id"])),
        axis=1,
    )
    out["pixel_x"] = pixels.map(lambda p: p[0])
    out["pixel_y"] = pixels.map(lambda p: p[1])

    out = out.dropna(subset=["pixel_x", "pixel_y"])
    return out


DF_ALL = _load_data()
MAP_OPTIONS = sorted(DF_ALL["map_id"].dropna().unique().tolist()) if not DF_ALL.empty else []


def _match_dataframe(map_id: str, date: str, match_id: str) -> pd.DataFrame:
    if DF_ALL.empty or not map_id or not date or not match_id:
        return DF_ALL.iloc[0:0]
    return DF_ALL[
        (DF_ALL["map_id"] == map_id) & (DF_ALL["date"] == date) & (DF_ALL["match_id"] == match_id)
    ]


def _axis_style() -> dict:
    return dict(
        autorange=False,
        visible=True,
        fixedrange=True,
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
        title="",
    )


def _empty_figure() -> go.Figure:
    fig = go.Figure()
    fig.update_xaxes(range=[0, 1024], **_axis_style())
    fig.update_yaxes(range=[1024, 0], **_axis_style())
    fig.update_layout(
        template="plotly_dark",
        uirevision=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig




app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], title="LILA · Journey Visualizer")
server = app.server

default_map = MAP_OPTIONS[0] if MAP_OPTIONS else None
default_dates = (
    sorted(DF_ALL.loc[DF_ALL["map_id"] == default_map, "date"].dropna().unique().tolist())
    if default_map is not None
    else []
)
default_date = default_dates[0] if default_dates else None
default_matches = (
    sorted(
        DF_ALL.loc[
            (DF_ALL["map_id"] == default_map) & (DF_ALL["date"] == default_date),
            "match_id",
        ]
        .dropna()
        .unique()
        .tolist()
    )
    if default_date is not None
    else []
)
default_match = default_matches[0] if default_matches else None

app.layout = html.Div(
    id="app-shell",
    children=[
        # ══ SIDEBAR ═══════════════════════════════════════════════════════════
        html.Div(
            id="sidebar",
            children=[
                # Logo / title
                html.Div(
                    id="sidebar-header",
                    children=[
                        html.H4("LILA"),
                        html.P("Journey Visualizer"),
                    ],
                ),
                # Filter controls
                html.Div(
                    id="sidebar-body",
                    children=[
                        # Map filter
                        html.Div(className="filter-section", children=[
                            html.Span("Map", className="filter-label"),
                            dcc.Dropdown(
                                id="map-dropdown",
                                options=[{"label": x, "value": x} for x in MAP_OPTIONS],
                                value=default_map,
                                clearable=False,
                                className="dash-dropdown",
                            ),
                        ]),
                        # Date filter
                        html.Div(className="filter-section", children=[
                            html.Span("Date", className="filter-label"),
                            dcc.Dropdown(id="date-dropdown", clearable=False, className="dash-dropdown"),
                        ]),
                        # Match ID filter
                        html.Div(className="filter-section", children=[
                            html.Span("Match ID", className="filter-label"),
                            dcc.Dropdown(id="match-dropdown", clearable=False, className="dash-dropdown"),
                        ]),
                        html.Div(className="sidebar-divider"),
                        # Entity toggles
                        html.Div(className="filter-section", children=[
                            html.Span("Entities", className="filter-label"),
                            dbc.Checklist(
                                id="entity-checklist",
                                options=[
                                    {"label": " Humans", "value": "humans"},
                                    {"label": " Bots",   "value": "bots"},
                                ],
                                value=["humans", "bots"],
                                switch=True,
                            ),
                        ]),
                        html.Div(className="sidebar-divider"),
                        # Heatmap toggles
                        html.Div(className="filter-section", children=[
                            html.Span("Heatmap", className="filter-label"),
                            dbc.Checklist(
                                id="heatmap-toggle",
                                options=[{"label": " Enable", "value": "heatmap"}],
                                value=[],
                                switch=True,
                            ),
                        ]),
                        html.Div(className="filter-section", children=[
                            html.Span("Heatmap Type", className="filter-label"),
                            dcc.Dropdown(
                                id="heatmap-mode",
                                options=[
                                    {"label": "Traffic Density", "value": "traffic"},
                                    {"label": "Death Density",   "value": "death"},
                                ],
                                value="traffic",
                                clearable=False,
                                className="dash-dropdown",
                            ),
                        ]),
                        html.Div(className="sidebar-divider"),
                        # Visual legend
                        html.Div(className="filter-section", children=[
                            html.Span("Legend", className="filter-label"),
                            html.Div(className="legend-row", children=[
                                html.Div(className="legend-line", style={"background": "#00FFFF"}),
                                html.Span("Human Path"),
                            ]),
                            html.Div(className="legend-row", children=[
                                html.Div(className="legend-line", style={"background": "#9CA3AF", "borderTop": "2px dashed #9CA3AF", "height": "0"}),
                                html.Span("Bot Path"),
                            ]),
                            html.Div(className="legend-row", children=[
                                html.Div(className="legend-dot", style={"background": "#39FF14"}),
                                html.Span("Kill"),
                            ]),
                            html.Div(className="legend-row", children=[
                                html.Div(className="legend-dot", style={"background": "#00F0FF"}),
                                html.Span("Loot"),
                            ]),
                            html.Div(className="legend-row", children=[
                                html.Div(className="legend-dot", style={"background": "#FF4444"}),
                                html.Span("Death"),
                            ]),
                            html.Div(className="legend-row", children=[
                                html.Div(className="legend-dot", style={"background": "#FF00FF"}),
                                html.Span("Storm Death"),
                            ]),
                        ]),
                    ],
                ),
            ],
        ),

        # ══ MAIN CONTENT ══════════════════════════════════════════════════════
        html.Div(
            id="main-content",
            children=[
                # ── Header Metric Cards ────────────────────────────────────────
                html.Div(
                    id="header-cards",
                    children=[
                        # Match ID card (wider)
                        html.Div(className="metric-card card-match", children=[
                            html.Div("Match ID", className="metric-label"),
                            html.Div(id="card-match-id", children="—",
                                     className="metric-value mono cyan"),
                        ]),
                        # Players
                        html.Div(className="metric-card card-player", children=[
                            html.Div("Players", className="metric-label"),
                            html.Div(id="card-player-count", children="—",
                                     className="metric-value cyan"),
                        ]),
                        # Bots
                        html.Div(className="metric-card card-bot", children=[
                            html.Div("Bots", className="metric-label"),
                            html.Div(id="card-bot-count", children="—",
                                     className="metric-value slate"),
                        ]),
                        # Total Events -> Events at T-Current
                        html.Div(className="metric-card card-events", children=[
                            html.Div("Events at T-Current", className="metric-label"),
                            html.Div(id="card-event-count", children="—",
                                     className="metric-value amber"),
                        ]),
                        # Survival Rate
                        html.Div(className="metric-card card-survival", children=[
                            html.Div("Survival Rate", className="metric-label"),
                            html.Div(id="card-survival-rate", children="—",
                                     className="metric-value green"),
                        ]),
                        # Duration
                        html.Div(className="metric-card card-dur", children=[
                            html.Div("Duration", className="metric-label"),
                            html.Div(id="card-duration", children="—",
                                     className="metric-value purple"),
                        ]),
                    ],
                ),

                # ── Map (flex-grow) ────────────────────────────────────────────
                html.Div(
                    id="map-area",
                    children=[
                        dcc.Graph(
                            id="map-graph",
                            figure=_empty_figure(),
                            config={"displaylogo": False, "scrollZoom": True},
                            style={"width": "100%", "height": "100%"},
                            responsive=True,
                        ),
                    ],
                ),

                # ── Timeline Strip ─────────────────────────────────────────────
                html.Div(
                    id="timeline-strip",
                    children=[
                        html.Div(
                            className="timeline-top-row",
                            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                            children=[
                                html.Div(
                                    id="timeline-label",
                                    children="Match Playback Timeline — select a match to begin",
                                ),
                                html.Button(
                                    "▶ Play",
                                    id="play-button",
                                    className="play-btn",
                                ),
                            ]
                        ),
                        dcc.Slider(
                            id="time-slider",
                            min=0,
                            max=1,
                            step=1,
                            value=0,
                            updatemode="drag",
                            tooltip={"always_visible": True, "placement": "top"},
                        ),
                        dcc.Interval(id="play-interval", interval=100, n_intervals=0, disabled=True),
                    ],
                ),
            ],
        ),

        # ── Client-side stores (invisible) ────────────────────────────────────
        dcc.Store(id="match-data-store"),
        dcc.Store(id="base-fig-store"),
    ],
)


@app.callback(
    Output("card-match-id", "children"),
    Output("card-player-count", "children"),
    Output("card-bot-count", "children"),
    Output("card-duration", "children"),
    Output("match-data-store", "data"),
    Output("base-fig-store", "data"),
    Input("match-dropdown", "value"),
    Input("map-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_metric_cards(selected_match, selected_map, selected_date):
    """Fires once on match selection. Populates metric cards AND the two data
    stores used by the clientside callback for zero-latency slider scrubbing."""
    empty = ("\u2014", "\u2014", "\u2014", "\u2014", None, None)
    if not selected_match or not selected_map or not selected_date or DF_ALL.empty:
        return empty
    df = _match_dataframe(selected_map, selected_date, selected_match)
    if df.empty:
        return empty

    # ── Metric card values ───────────────────────────────────────────────────
    short_id      = selected_match[:36]
    player_count  = int(df[df["is_bot"] == False]["user_id"].nunique())
    bot_count     = int(df[df["is_bot"] == True]["user_id"].nunique())
    event_count   = len(df)
    duration_ms   = int(df["relative_ms"].max()) if "relative_ms" in df.columns else 0

    # ── match-data-store: columnar payload for the clientside callback ────────
    # Dynamic downsampling: stride=2 when position rows > 500 to halve render cost.
    pos_mask   = df["event"].isin(["Position", "BotPosition"])
    n_pos      = pos_mask.sum()
    stride     = 2 if n_pos > 500 else 1
    pos_rows   = df[pos_mask].iloc[::stride]  # downsampled path rows
    event_rows = df[~pos_mask]                # ALL event markers kept
    serialise  = pd.concat([pos_rows, event_rows]).sort_values("relative_ms")

    match_payload = {
        "relative_ms": serialise["relative_ms"].astype(int).tolist(),
        "pixel_x":     serialise["pixel_x"].round(2).tolist(),
        "pixel_y":     serialise["pixel_y"].round(2).tolist(),
        "event":       serialise["event"].tolist(),
        "user_id":     serialise["user_id"].tolist(),
        "is_bot":      serialise["is_bot"].tolist(),
        "total_players": player_count,
    }

    # ── base-fig-store: layout with background minimap (no traces) ────────────
    # Cached per map_id; never re-encoded during scrubbing.
    base_layout = dict(
        template         = "plotly_dark",
        uirevision       = True,          # preserves zoom/pan across updates
        paper_bgcolor    = "rgba(0,0,0,0)",
        plot_bgcolor     = "rgba(0,0,0,0)",
        margin           = dict(l=0, r=0, t=0, b=0),
        legend           = dict(orientation="h", y=1.01, x=0),
        xaxis            = dict(range=[0, 1024], autorange=False, visible=True,
                                fixedrange=True, showticklabels=False,
                                showgrid=False, zeroline=False, showline=False,
                                ticks="", title=""),
        yaxis            = dict(range=[1024, 0], autorange=False, visible=True,
                                fixedrange=True, showticklabels=False,
                                showgrid=False, zeroline=False, showline=False,
                                ticks="", title=""),
    )
    try:
        img_uri = _get_map_image_uri(str(selected_map))  # server-side LRU cache
        base_layout["images"] = [dict(
            source  = img_uri,
            xref    = "x", yref="y",
            x=0, y=0,
            sizex   = 1024, sizey=1024,
            xanchor = "left", yanchor="top",
            sizing  = "stretch",
            opacity = 1.0,
            layer   = "below",
        )]
    except Exception:
        pass

    base_fig = {"data": [], "layout": base_layout}

    return (
        short_id, str(player_count), str(bot_count),
        f"{duration_ms}ms", match_payload, base_fig,
    )


@app.callback(
    Output("date-dropdown", "options"),
    Output("date-dropdown", "value"),
    Input("map-dropdown", "value"),
)
def update_dates(selected_map: str):
    if not selected_map or DF_ALL.empty:
        return [], None
    dates = sorted(DF_ALL.loc[DF_ALL["map_id"] == selected_map, "date"].dropna().unique().tolist())
    options = [{"label": d, "value": d} for d in dates]
    value = dates[0] if dates else None
    return options, value


@app.callback(
    Output("match-dropdown", "options"),
    Output("match-dropdown", "value"),
    Input("map-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_matches(selected_map: str, selected_date: str):
    if not selected_map or not selected_date or DF_ALL.empty:
        return [], None
    mask = (DF_ALL["map_id"] == selected_map) & (DF_ALL["date"] == selected_date)
    matches = sorted(DF_ALL.loc[mask, "match_id"].dropna().unique().tolist())
    options = [{"label": m, "value": m} for m in matches]
    value = matches[0] if matches else None
    return options, value


@app.callback(
    Output("time-slider", "min"),
    Output("time-slider", "max"),
    Output("time-slider", "value"),
    Output("time-slider", "marks"),
    Output("time-slider", "step"),
    Input("match-dropdown", "value"),
    Input("map-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_slider_init(selected_match, selected_map, selected_date):
    """CALLBACK 1 — Slider in milliseconds (matches are 50–900 ms of event data)."""
    if not selected_match or not selected_map or not selected_date or DF_ALL.empty:
        return 0, 100, 0, {0: "0ms", 100: "100ms"}, 1

    df = _match_dataframe(selected_map, selected_date, selected_match)
    if df.empty or "relative_ms" not in df.columns:
        return 0, 100, 0, {0: "0ms", 100: "100ms"}, 1

    max_ms = int(df["relative_ms"].max())
    if max_ms < 1:
        max_ms = 1

    # 5 evenly-spaced marks formatted as milliseconds.
    step_size = max(1, max_ms // 4)
    mark_positions = sorted({0, step_size, step_size * 2, step_size * 3, max_ms})
    marks = {pos: f"{pos}ms" for pos in mark_positions}

    # value=0 → map starts empty; user scrubs right to reveal events in order.
    return 0, max_ms, 0, marks, 1


@app.callback(
    Output("timeline-label", "children"),
    Input("time-slider", "value"),
    Input("match-dropdown", "value"),
    Input("map-dropdown", "value"),
    Input("date-dropdown", "value"),
)
def update_timeline_label(slider_value, selected_match, selected_map, selected_date):
    """Live label above the slider showing current scrub position in ms."""
    if not selected_match or slider_value is None:
        return "Match Playback Timeline — select a match to begin"
    sv = int(slider_value)
    df = _match_dataframe(selected_map or "", selected_date or "", selected_match)
    total = int(df["relative_ms"].max()) if not df.empty and "relative_ms" in df.columns else sv
    return f"Match Playback Timeline — {sv}ms / {total}ms elapsed"


# ── Clientside callback: runs in the browser, zero network latency on scrub ──
# Reads match-data-store + base-fig-store (populated once on match select).
# Filters relative_ms <= slider_value and rebuilds traces entirely in JS.
app.clientside_callback(
    ClientsideFunction(namespace="lila", function_name="updateGraph"),
    [
        Output("map-graph", "figure"),
        Output("card-event-count", "children"),
        Output("card-survival-rate", "children")
    ],
    Input("time-slider", "value"),
    Input("match-data-store", "data"),
    Input("base-fig-store", "data"),
    Input("entity-checklist", "value"),
    Input("heatmap-toggle", "value"),
    Input("heatmap-mode", "value"),
)

@app.callback(
    Output("play-interval", "disabled"),
    Output("play-button", "children"),
    Input("play-button", "n_clicks"),
    State("play-interval", "disabled"),
    prevent_initial_call=True
)
def toggle_play(n_clicks, is_disabled):
    if n_clicks:
        if is_disabled:
            return False, "⏸ Pause"
        else:
            return True, "▶ Play"
    return True, "▶ Play"

@app.callback(
    Output("time-slider", "value", allow_duplicate=True),
    Input("play-interval", "n_intervals"),
    State("time-slider", "value"),
    State("time-slider", "max"),
    prevent_initial_call=True
)
def auto_play_tick(n_intervals, current_val, max_val):
    if current_val is None:
        current_val = 0
    # Add roughly 1% of the timeline per tick, ensuring at least step=1
    step = max(1, max_val // 100)
    new_val = current_val + step
    if new_val >= max_val:
        return max_val
    return new_val


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
