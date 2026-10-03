import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import load_data, departamentos_disponibles

dash.register_page(__name__, path="/incidentes", name="Tablero de Incidentes", icon="📊")

AZUL = "#12192B"
CIAN = "#1CC9E8"
NARANJA = "#F2994A"
AMARILLO = "#F2C94C"
GRIS = "#4A5568"
VERDE = "#2E9E5B"
ROJO = "#D64545"

layout = html.Div(
    [
        html.Div("Incidentes por tipo, estado y cumplimiento de tiempos", className="page-title"),
        html.Div(
            "Obras y Permiso de Ingreso son los tipos de aviso con peor cumplimiento "
            "de tiempo (más del 68 % atrasados), mientras que Caldas y Tolima son los "
            "departamentos con mayor proporción de avisos atrasados.",
            className="page-subtitle",
        ),

        # ---- KPIs ----
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Total de avisos", className="kpi-label"),
                        html.Div(id="kpi-total", className="kpi-value"),
                    ],
                    className="kpi-card",
                ),
                html.Div(
                    [
                        html.Div("% Atrasados", className="kpi-label"),
                        html.Div(id="kpi-atrasado", className="kpi-value kpi-alert"),
                    ],
                    className="kpi-card",
                ),
                html.Div(
                    [
                        html.Div("Días abiertos (promedio)", className="kpi-label"),
                        html.Div(id="kpi-dias", className="kpi-value"),
                    ],
                    className="kpi-card",
                ),
                html.Div(
                    [
                        html.Div(id="kpi4-label", className="kpi-label"),
                        html.Div(id="kpi4-value", className="kpi-value"),
                    ],
                    className="kpi-card",
                ),
            ],
            className="kpi-row",
        ),

html.Div(
    [
        html.Div(
            [
                html.Div("Departamento", className="filter-label"),
                dcc.Dropdown(
                    id="filtro-departamento",
                    options=[{"label": "Todos", "value": "Todos"}]
                    + [{"label": d, "value": d} for d in departamentos_disponibles()],
                    value="Todos",
                    clearable=False,
                ),
            ],
            className="filter-item",
        ),
        html.Div(
            [
                html.Div(className="filter-label", style={"visibility": "hidden"}, children="."),
                html.Button("✕ Limpiar filtros", id="boton-limpiar-filtros", className="clear-button"),
            ],
            className="filter-item",
        ),
    ],
    className="filter-row",
),
        html.Div(
            [
                html.Div(
                    [
                        html.H4("Avisos por tipo y estado"),
                        html.P(
                            "Barras agrupadas · haz clic en un tipo de aviso para resaltarlo "
                            "en el gráfico de la derecha y en los KPIs.",
                            style={"fontSize": "12px", "color": GRIS},
                        ),
                        dcc.Graph(id="grafico-barras-agrupadas"),
                    ],
                    className="card",
                ),
                html.Div(
                    [
                        html.H4("Cumplimiento de tiempo por departamento"),
                        html.P(
                            "Barras divergentes · % a tiempo (derecha) vs. % atrasado (izquierda). "
                            "Haz clic en un departamento para filtrar todo el tablero por esa zona.",
                            style={"fontSize": "12px", "color": GRIS},
                        ),
                        dcc.Graph(id="grafico-barras-divergentes"),
                    ],
                    className="card",
                ),
            ],
            className="content-grid",
        ),
    ]
)


def filtra(df: pd.DataFrame, departamento: str) -> pd.DataFrame:
    if departamento and departamento != "Todos":
        return df[df["Departamento"] == departamento]
    return df


def filtra_tipo(df: pd.DataFrame, click_data) -> pd.DataFrame:
    if click_data:
        tipo = click_data["points"][0]["x"]
        return df[df["Tipo de aviso"] == tipo]
    return df


# ---- Click en un departamento del gráfico divergente -> actualiza el dropdown ----
@callback(
    Output("filtro-departamento", "value", allow_duplicate=True),
    Output("grafico-barras-agrupadas", "clickData"),
    Input("boton-limpiar-filtros", "n_clicks"),
    prevent_initial_call=True,
)
def limpiar_filtros(n_clicks):
    return "Todos", None
@callback(
    Output("filtro-departamento", "value"),
    Input("grafico-barras-divergentes", "clickData"),
    prevent_initial_call=True,
)

def actualizar_filtro_desde_divergente(click_data):
    if click_data:
        departamento = click_data["points"][0]["y"]
        if departamento != "Sin dato":
            return departamento
    return dash.no_update

NARANJA_SUAVE = "#FBE3C8"
AZUL_SUAVE = "#C3C9D4"

@callback(
    Output("grafico-barras-agrupadas", "figure"),
    Input("filtro-departamento", "value"),
    Input("grafico-barras-agrupadas", "clickData"),
)
def actualizar_barras_agrupadas(departamento, click_data):
    df = filtra(load_data(), departamento)

    conteo = (
        df.groupby(["Tipo de aviso", "Estado aviso"]).size().reset_index(name="Avisos")
    )

    tipo_resaltado = None
    if click_data:
        tipo_resaltado = click_data["points"][0]["x"]

    fig = go.Figure()
    for estado, color_full, color_suave in [
        ("Abierto", NARANJA, NARANJA_SUAVE),
        ("Cerrado", AZUL, AZUL_SUAVE),
    ]:
        sub = conteo[conteo["Estado aviso"] == estado]
        colores = [
            color_full if (tipo_resaltado is None or t == tipo_resaltado) else color_suave
            for t in sub["Tipo de aviso"]
        ]
        fig.add_bar(
            x=sub["Tipo de aviso"],
            y=sub["Avisos"],
            name=estado,
            marker_color=colores,
            hovertemplate="<b>%{x}</b><br>" + estado + ": %{y} avisos<extra></extra>",
        )

    fig.update_layout(
        barmode="group",
        template="plotly_white",
        xaxis=dict(automargin=True),
        margin=dict(t=10, l=10, r=10, b=60),
        legend=dict(orientation="h", y=1.15),
        transition={"duration": 400, "easing": "cubic-in-out"},
        height=380,
    )
    return fig

@callback(
    Output("grafico-barras-divergentes", "figure"),
    Input("filtro-departamento", "value"),
    Input("grafico-barras-agrupadas", "clickData"),
)
def actualizar_barras_divergentes(departamento, click_data):
    df = filtra_tipo(load_data(), click_data)
    df = filtra(df, departamento)

    tab = (
        pd.crosstab(df["Departamento"], df["Tiempo aviso"], normalize="index") * 100
    ).round(1)
    tab["n"] = df.groupby("Departamento").size()
    tab = tab[tab["n"] >= 5].sort_values("Atrasado", ascending=True)

    fig = go.Figure()
    fig.add_bar(
        y=tab.index,
        x=-tab.get("Atrasado", pd.Series(0, index=tab.index)),
        name="Atrasado",
        orientation="h",
        marker_color=NARANJA,
        hovertemplate="<b>%{y}</b><br>Atrasado: %{customdata:.1f}%<extra></extra>",
        customdata=tab.get("Atrasado", pd.Series(0, index=tab.index)),
    )
    fig.add_bar(
        y=tab.index,
        x=tab.get("A tiempo", pd.Series(0, index=tab.index)),
        name="A tiempo",
        orientation="h",
        marker_color=CIAN,
        hovertemplate="<b>%{y}</b><br>A tiempo: %{x:.1f}%<extra></extra>",
    )

    fig.add_vline(x=0, line_width=1, line_color=GRIS)

    fig.update_layout(
        barmode="relative",
        template="plotly_white",
        margin=dict(t=10, l=10, r=10, b=10),
        legend=dict(orientation="h", y=1.15),
        xaxis_title="% de avisos",
        transition={"duration": 400, "easing": "cubic-in-out"},
        height= max(220, 55 * len(tab)),
    )
    return fig


@callback(
    Output("kpi-total", "children"),
    Output("kpi-atrasado", "children"),
    Output("kpi-dias", "children"),
    Output("kpi4-label", "children"),
    Output("kpi4-value", "children"),
    Input("filtro-departamento", "value"),
    Input("grafico-barras-agrupadas", "clickData"),
)
def actualizar_kpis(departamento, click_data):
    df = filtra(load_data(), departamento)
    df_tipo = filtra_tipo(df, click_data)

    total = len(df_tipo)
    pct_atrasado = (df_tipo["Tiempo aviso"] == "Atrasado").mean() * 100 if total else 0
    dias_promedio = df_tipo["Días abierto"].mean() if total else 0

    if click_data:
        # Ya hay un tipo seleccionado -> mostramos el departamento con más avisos de ese tipo
        top = df_tipo["Departamento"].value_counts()
        kpi4_label = "Depto. con más avisos de este tipo"
    else:
        top = df_tipo["Tipo de aviso"].value_counts()
        kpi4_label = "Tipo de aviso más frecuente"

    if len(top):
        kpi4_value = f"{top.index[0]} ({top.iloc[0]})"
    else:
        kpi4_value = "—"

    return (
        f"{total:,}".replace(",", "."),
        f"{pct_atrasado:.1f}%",
        f"{dias_promedio:.0f} días",
        kpi4_label,
        kpi4_value,
    )