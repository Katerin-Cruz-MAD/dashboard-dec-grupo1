import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import load_data, departamentos_disponibles

dash.register_page(__name__, path="/incidentes", name="Tablero de Incidentes", icon="📊")

AZUL = "#0B1F3A"
AMBAR = "#F2A93B"
VERDE = "#2E9E5B"
ROJO = "#D64545"
GRIS = "#4A5568"

layout = html.Div(
    [
        html.Div("Incidentes por tipo, estado y cumplimiento de tiempos", className="page-title"),
        html.Div(
            "Obras y Permiso de Ingreso son los tipos de aviso con peor cumplimiento "
            "de tiempo (más del 68 % atrasados), mientras que Caldas y Tolima son los "
            "departamentos con mayor proporción de avisos atrasados.",
            className="page-subtitle",
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
                            "en el gráfico de cumplimiento por departamento.",
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
                            "Barras divergentes · % a tiempo (derecha) vs. % atrasado (izquierda).",
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
    for estado, color in [("Abierto", AMBAR), ("Cerrado", AZUL)]:
        sub = conteo[conteo["Estado aviso"] == estado]
        opacidades = [
            1.0 if (tipo_resaltado is None or t == tipo_resaltado) else 0.25
            for t in sub["Tipo de aviso"]
        ]
        fig.add_bar(
            x=sub["Tipo de aviso"],
            y=sub["Avisos"],
            name=estado,
            marker_color=color,
            marker_opacity=opacidades,
            hovertemplate="<b>%{x}</b><br>" + estado + ": %{y} avisos<extra></extra>",
        )

    fig.update_layout(
        barmode="group",
        template="plotly_white",
        margin=dict(t=10, l=10, r=10, b=10),
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
    df = load_data()

    if click_data:
        tipo = click_data["points"][0]["x"]
        df = df[df["Tipo de aviso"] == tipo]

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
        marker_color=ROJO,
        hovertemplate="<b>%{y}</b><br>Atrasado: %{customdata:.1f}%<extra></extra>",
        customdata=tab.get("Atrasado", pd.Series(0, index=tab.index)),
    )
    fig.add_bar(
        y=tab.index,
        x=tab.get("A tiempo", pd.Series(0, index=tab.index)),
        name="A tiempo",
        orientation="h",
        marker_color=VERDE,
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
        height=380,
    )
    return fig
