import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import load_data, ctes_disponibles

dash.register_page(__name__, path="/flujos", name="Tablero de Flujos", icon="🔀")

AZUL = "#0B1F3A"
AMBAR = "#F2A93B"
GRIS = "#4A5568"
PALETA_DEP = ["#0B1F3A", "#12315C", "#2E6E9E", "#4F9DBB", "#7CC6C0", "#F2A93B"]
PALETA_TIPO = ["#D64545", "#F2A93B", "#2E9E5B", "#4F9DBB", "#8E6CB0"]

TOP_N_DEPARTAMENTOS = 6

layout = html.Div(
    [
        html.Div("Relación entre zona geográfica, tipo de aviso y estado", className="page-title"),
        html.Div(
            "El 55 % de los avisos del CTE Centro están atrasados, frente al 49 % en "
            "Suroccidente. El flujo muestra cómo se reparten los avisos de los 6 "
            "departamentos con mayor volumen entre los distintos tipos y su estado final.",
            className="page-subtitle",
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Div("CTE", className="filter-label"),
                        dcc.Dropdown(
                            id="filtro-cte",
                            options=[{"label": "Todos", "value": "Todos"}]
                            + [{"label": c, "value": c} for c in ctes_disponibles()],
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
                        html.H4("Flujo: Departamento → Tipo de aviso → Estado"),
                        html.P(
                            "Se muestran los 6 departamentos con mayor volumen de avisos. "
                            "Pasa el cursor sobre un flujo para ver el detalle.",
                            style={"fontSize": "12px", "color": GRIS},
                        ),
                        dcc.Graph(id="grafico-sankey"),
                    ],
                    className="card card-full",
                ),
                html.Div(
                    [
                        html.H4("Perfil de los avisos: tiempos y prioridad"),
                        html.P(
                            "Coordenadas paralelas · cada línea es un aviso; el color indica "
                            "si se atendió a tiempo (verde) o atrasado (rojo).",
                            style={"fontSize": "12px", "color": GRIS},
                        ),
                        dcc.Graph(id="grafico-parcoords"),
                    ],
                    className="card card-full",
                ),
            ],
            className="content-grid",
        ),
    ]
)


def filtra_cte(df: pd.DataFrame, cte: str) -> pd.DataFrame:
    if cte and cte != "Todos":
        return df[df["CTE"] == cte]
    return df


@callback(Output("grafico-sankey", "figure"), Input("filtro-cte", "value"))
def actualizar_sankey(cte):
    df = filtra_cte(load_data(), cte)

    top_deps = df["Departamento"].value_counts().head(TOP_N_DEPARTAMENTOS).index.tolist()
    df = df[df["Departamento"].isin(top_deps)]

    tipos = sorted(df["Tipo de aviso"].unique().tolist())
    estados = ["Abierto", "Cerrado"]

    nodos = top_deps + tipos + estados
    idx = {n: i for i, n in enumerate(nodos)}

    colores_nodo = (
        [PALETA_DEP[i % len(PALETA_DEP)] for i in range(len(top_deps))]
        + [PALETA_TIPO[i % len(PALETA_TIPO)] for i in range(len(tipos))]
        + [AMBAR, AZUL]
    )

    flujo1 = df.groupby(["Departamento", "Tipo de aviso"]).size().reset_index(name="valor")
    flujo2 = df.groupby(["Tipo de aviso", "Estado aviso"]).size().reset_index(name="valor")

    source, target, value = [], [], []
    for _, r in flujo1.iterrows():
        source.append(idx[r["Departamento"]])
        target.append(idx[r["Tipo de aviso"]])
        value.append(r["valor"])
    for _, r in flujo2.iterrows():
        source.append(idx[r["Tipo de aviso"]])
        target.append(idx[r["Estado aviso"]])
        value.append(r["valor"])

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=nodos,
                color=colores_nodo,
                pad=16,
                thickness=18,
                line=dict(color="white", width=0.5),
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color="rgba(11,31,58,0.15)",
                hovertemplate="%{source.label} → %{target.label}<br>%{value} avisos<extra></extra>",
            ),
        )
    )
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        height=420,
        font=dict(size=12, color=AZUL),
    )
    return fig


@callback(Output("grafico-parcoords", "figure"), Input("filtro-cte", "value"))
def actualizar_parcoords(cte):
    df = filtra_cte(load_data(), cte).copy()

    df["tiempo_num"] = (df["Tiempo aviso"] == "Atrasado").astype(int)

    fig = go.Figure(
        go.Parcoords(
            line=dict(
                color=df["tiempo_num"],
                colorscale=[[0, "#2E9E5B"], [1, "#D64545"]],
                showscale=True,
                colorbar=dict(
                    tickvals=[0, 1],
                    ticktext=["A tiempo", "Atrasado"],
                    title="Cumplimiento",
                ),
            ),
            dimensions=[
                dict(label="Días abierto", values=df["Días abierto"]),
                dict(label="Prioridad (días)", values=df["Prioridad días"]),
                dict(label="Trimestre aviso", values=df["Trimestre"], tickvals=[1, 2, 3, 4]),
                dict(
                    label="Desviación vs. prioridad",
                    values=df["Cumple prioridad periodos"].fillna(0),
                ),
            ],
        )
    )
    fig.update_layout(margin=dict(t=40, l=60, r=40, b=10), height=420)
    return fig
