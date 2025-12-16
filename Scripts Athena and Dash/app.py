import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import warnings

from data_loader import load_data

# =========================
# 1) LOAD DATA
# =========================
warnings.filterwarnings("ignore")
print("Chargement des données depuis Athena (cela peut prendre quelques secondes/minutes...)")
df_global = load_data()
print("Données chargées et moyennes mobiles calculées.")

if df_global.empty:
    raise RuntimeError(
        "Le DataFrame est vide. Vérifie les clés AWS, la requête SQL et la connexion dans data_loader.py."
    )

ticker_list = sorted(df_global["ticker"].unique())
min_date = df_global["transaction_date"].min().date()
max_date = df_global["transaction_date"].max().date()

# =========================
# 2) DASH APP
# =========================
app = dash.Dash(__name__)
app.title = "Analyse de tendance boursière (AWS)"


# =========================
# Helpers (fig styling)
# =========================
def style_fig(fig, title=None, ytitle=None, xtitle=None):
    fig.update_layout(
        template="plotly_dark",
        title=title,
        yaxis_title=ytitle,
        xaxis_title=xtitle,
        legend_title="Indicateur",
        hovermode="x unified",

        # ✅ Tooltip lisible en thème dark
        hoverlabel=dict(
            bgcolor="#0f1a2e",
            bordercolor="#7c5cff",
            font=dict(color="#eaf0ff", size=13),
        ),

        margin=dict(l=12, r=12, t=52 if title else 24, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#eaf0ff"),
        xaxis=dict(gridcolor="rgba(234,240,255,0.08)"),
        yaxis=dict(gridcolor="rgba(234,240,255,0.08)"),
    )
    return fig


def empty_fig(message="—"):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin=dict(l=12, r=12, t=30, b=12),
        annotations=[{
            "text": message,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 14, "color": "rgba(234,240,255,0.75)"},
        }],
    )
    return fig


# =========================
# 3) LAYOUT
# =========================
section_title_style = {
    "fontWeight": "900",
    "letterSpacing": "-0.01em",
    "marginBottom": "10px",
    "marginTop": "0px",
}

app.layout = html.Div(className="app-container", children=[
    # Header
    html.Div(className="header", children=[
        html.H1("Analyse de tendance boursière (AWS)", className="title"),
        html.P(
            "Suivi des prix, MM50/MM200, volatilité et drawdown (lecture monitoring).",
            className="subtitle"
        ),
    ]),
    html.Div(className="divider"),

    # Filters (blur ONLY here) + z-index safe
    html.Div(
        className="card card-pad filters-card",
        style={"zIndex": 9999, "position": "relative"},
        children=[
            html.Div(className="filters", children=[
                html.Div(className="filter-block", children=[
                    html.Label("Actif (Ticker)"),
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[{"label": i, "value": i} for i in ticker_list],
                        value=ticker_list[0] if ticker_list else None,
                        multi=False,
                        clearable=False,
                    ),
                ]),
                html.Div(className="filter-block", children=[
                    html.Label("Période"),
                    dcc.DatePickerRange(
                        id="date-range",
                        start_date=min_date,
                        end_date=max_date,
                        display_format="YYYY-MM-DD",
                        minimum_nights=0,
                        show_outside_days=True,
                    ),
                ]),
            ])
        ]
    ),

    # Main block: KPIs + Price/MM chart
    html.Div(className="card card-pad", style={"marginTop": "14px"}, children=[
        html.Div(className="kpi-row", children=[
            html.Div(id="kpi-price", className="kpi-card"),
            html.Div(id="kpi-change", className="kpi-card"),
            html.Div(id="kpi-mm-status", className="kpi-card"),
            html.Div(id="kpi-vol", className="kpi-card"),
            html.Div(id="kpi-dd", className="kpi-card"),
        ]),
        html.Div(className="graph-card", children=[
            dcc.Graph(
                id="price-chart",
                config={
                    "displayModeBar": True,     # ✅ barre d'outils
                    "displaylogo": False,
                    "scrollZoom": True,         # ✅ zoom molette
                    # Optionnel: enlève 2/3 boutons pas utiles
                    "modeBarButtonsToRemove": ["lasso2d", "select2d"]
                }
            )
        ]),
    ]),

    # Auto summary
    html.Div(className="card card-pad", style={"marginTop": "14px"}, children=[
        html.Div("Résumé automatique", style=section_title_style),
        html.P(id="summary-text", style={
            "marginTop": "8px",
            "marginBottom": "0px",
            "color": "rgba(234,240,255,0.82)",
            "lineHeight": "1.5",
            "fontSize": "13px",
        }),
    ]),

    html.Div(className="divider"),

    # Footer
    html.Div(className="footer", children=[
        html.Div(f"Source : {len(ticker_list)} actifs chargés depuis AWS Athena."),
        html.Div("Indicateurs : close, MM50, MM200, Daily_Return, Volatilité (σ), Max Drawdown (DD)."),
    ]),
])


# =========================
# 4) CALLBACK
# =========================
@app.callback(
    [
        Output("price-chart", "figure"),
        Output("kpi-price", "children"),
        Output("kpi-change", "children"),
        Output("kpi-mm-status", "children"),
        Output("kpi-vol", "children"),
        Output("kpi-dd", "children"),
        Output("summary-text", "children"),
    ],
    [
        Input("ticker-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_dashboard(selected_ticker, start_date, end_date):
    placeholder_kpi = html.Div("—")

    if not selected_ticker:
        ef = empty_fig("Sélectionne un ticker")
        return ef, placeholder_kpi, placeholder_kpi, placeholder_kpi, placeholder_kpi, placeholder_kpi, "—"

    filtered_df = df_global[df_global["ticker"] == selected_ticker].copy()

    if start_date:
        filtered_df = filtered_df[filtered_df["transaction_date"] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df["transaction_date"] <= pd.to_datetime(end_date)]

    if filtered_df.empty:
        ef = empty_fig("Aucune donnée pour la période sélectionnée")
        return ef, placeholder_kpi, placeholder_kpi, placeholder_kpi, placeholder_kpi, placeholder_kpi, (
            "Aucune donnée disponible sur cette période. Essaye d’élargir la plage de dates."
        )

    first_close = float(filtered_df["close"].iloc[0])
    last_close = float(filtered_df["close"].iloc[-1])
    pct_change = ((last_close - first_close) / first_close * 100) if first_close else 0.0

    last_mm50 = float(filtered_df["MM50"].iloc[-1])
    last_mm200 = float(filtered_df["MM200"].iloc[-1])
    is_bull = last_mm50 > last_mm200
    mm_status = "Bullish (MM50 > MM200)" if is_bull else "Bearish (MM50 ≤ MM200)"

    returns = filtered_df["Daily_Return"].dropna()
    volatility = float(returns.std() * 100) if not returns.empty else 0.0

    max_dd = 0.0
    if not returns.empty:
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.cummax()
        drawdown = (cum_returns / rolling_max) - 1
        max_dd = float(drawdown.min() * 100)

    # KPIs
    kpi_price = html.Div([
        html.Div(className="kpi-left", children=[
            html.Div("Prix actuel", className="kpi-title"),
            html.Div(f"{last_close:,.2f} €", className="kpi-value"),
        ]),
        html.Div("Close", className="kpi-badge"),
    ])

    change_badge_class = "kpi-badge badge-up" if pct_change >= 0 else "kpi-badge badge-down"
    kpi_change = html.Div([
        html.Div(className="kpi-left", children=[
            html.Div("Variation", className="kpi-title"),
            html.Div(f"{pct_change:+.2f}%", className="kpi-value"),
        ]),
        html.Div("↑" if pct_change >= 0 else "↓", className=change_badge_class),
    ])

    mm_badge_class = "kpi-badge badge-bull" if is_bull else "kpi-badge badge-bear"
    kpi_mm = html.Div([
        html.Div(className="kpi-left", children=[
            html.Div("Tendance MM", className="kpi-title"),
            html.Div(mm_status, className="kpi-value"),
        ]),
        html.Div("Bull" if is_bull else "Bear", className=mm_badge_class),
    ])

    kpi_vol = html.Div([
        html.Div(className="kpi-left", children=[
            html.Div("Volatilité", className="kpi-title"),
            html.Div(f"{volatility:.2f} %", className="kpi-value"),
        ]),
        html.Div("σ", className="kpi-badge"),
    ])

    kpi_dd = html.Div([
        html.Div(className="kpi-left", children=[
            html.Div("Max Drawdown", className="kpi-title"),
            html.Div(f"{max_dd:.2f} %", className="kpi-value"),
        ]),
        html.Div("DD", className="kpi-badge"),
    ])

    # Graph price + MMs
    fig = px.line(filtered_df, x="transaction_date", y=["close", "MM50", "MM200"])

    # Renommage + hovertemplate propre
    for tr in fig.data:
        if tr.name == "close":
            tr.name = "Close"
        elif tr.name == "MM50":
            tr.name = "MM50"
        elif tr.name == "MM200":
            tr.name = "MM200"

        tr.hovertemplate = (
            "<b>%{fullData.name}</b><br>"
            "Date : %{x|%Y-%m-%d}<br>"
            "Valeur : %{y:.2f} €<br>"
            "<extra></extra>"
        )

    fig = style_fig(
        fig,
        title=f"{selected_ticker} — Prix & Moyennes Mobiles (MM50 vs MM200)",
        ytitle="Prix (€)",
        xtitle="Date",
    )

    # Résumé auto
    risk_level = "faible" if volatility < 1 else ("modéré" if volatility < 2 else "élevé")
    summary = (
        f"Sur la période sélectionnée, {selected_ticker} affiche une performance de {pct_change:+.2f} %. "
        f"La tendance est {'haussière' if is_bull else 'baissière'} selon MM50/MM200. "
        f"Le risque est jugé {risk_level} (volatilité σ = {volatility:.2f} %). "
        f"Le drawdown maximal observé est de {max_dd:.2f} %."
    )

    return fig, kpi_price, kpi_change, kpi_mm, kpi_vol, kpi_dd, summary


# =========================
# 5) RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
