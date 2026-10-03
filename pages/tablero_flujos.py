import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import load_data, ctes_disponibles

dash.register_page(__name__, path="/flujos", name="Tablero de Flujos", icon="🔀")

AZUL = "#12192B"
CIAN = "#1CC9E8"
NARANJA = "#F2994A"
AMARILLO = "#F2C94C"
GRIS = "#4A5568"
PALETA_DEP = ["#12192B", "#1CC9E8", "#4A5568", "#F2994A", "#F2C94C", "#5B7DB1"]
PALETA_TIPO = ["#F2994A", "#1CC9E8", "#F2C94C", "#4A5568", "#5B7DB1"]

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

        # ---- KPIs ----
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Total de avisos", className="kpi-label"),
                        html.Div(id="kpi-flujos-total", className="kpi-value"),
                    ],
                    className="kpi-card",
                ),
                html.Div(
                    [
                        html.Div("% Atrasados", className="kpi-label"),
                        html.Div(id="kpi-flujos-atrasado", className="kpi-value kpi-alert"),
                    ],
                    className="kpi-card",
                ),
                html.Div(
                    [
                        html.Div("Departamento con más avisos", className="kpi-label"),
                        html.Div(id="kpi-flujos-top-depto", className="kpi-value"),
                    ],
                    className="kpi-card",
                ),
                html.Div(
                    [
                        html.Div("Tipo de aviso más frecuente", className="kpi-label"),
                        html.Div(id="kpi-flujos-top-tipo", className="kpi-value"),
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
                html.Div(
                    [
                        html.Div(className="filter-label", style={"visibility": "hidden"}, children="."),
                        html.Button("✕ Limpiar filtros", id="boton-limpiar-filtros-flujos", className="clear-button"),
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


@callback(
    Output("filtro-cte", "value", allow_duplicate=True),
    Input("boton-limpiar-filtros-flujos", "n_clicks"),
    prevent_initial_call=True,
)
def limpiar_filtros_flujos(n_clicks):
    return "Todos"


@callback(
    Output("kpi-flujos-total", "children"),
    Output("kpi-flujos-atrasado", "children"),
    Output("kpi-flujos-top-depto", "children"),
    Output("kpi-flujos-top-tipo", "children"),
    Input("filtro-cte", "value"),
)
def actualizar_kpis_flujos(cte):
    df = filtra_cte(load_data(), cte)

    total = len(df)
    pct_atrasado = (df["Tiempo aviso"] == "Atrasado").mean() * 100 if total else 0

    top_depto = df["Departamento"].value_counts()
    top_tipo = df["Tipo de aviso"].value_counts()

    depto_txt = f"{top_depto.index[0]} ({top_depto.iloc[0]})" if len(top_depto) else "—"
    tipo_txt = f"{top_tipo.index[0]} ({top_tipo.iloc[0]})" if len(top_tipo) else "—"

    return (
        f"{total:,}".replace(",", "."),
        f"{pct_atrasado:.1f}%",
        depto_txt,
        tipo_txt,
    )


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
        + [NARANJA, AZUL]
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
                color="rgba(18,25,43,0.15)",
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


PRIORIDAD_ORDEN = ["Semana", "Mes", "Trimestre", "Semestre", "Año", "Dos años", "Tres años", "Seis años"]
PRIORIDAD_CODIGO = {nombre: i + 1 for i, nombre in enumerate(PRIORIDAD_ORDEN)}


@callback(Output("grafico-parcoords", "figure"), Input("filtro-cte", "value"))
def actualizar_parcoords(cte):
    df = filtra_cte(load_data(), cte).copy()

    df = df[df["Prioridad"].isin(PRIORIDAD_ORDEN)]

    df["tiempo_num"] = (df["Tiempo aviso"] == "Atrasado").astype(int)
    df["prioridad_num"] = df["Prioridad"].map(PRIORIDAD_CODIGO)
    df["dias_abierto_cap"] = df["Días abierto"].clip(upper=730)

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
                dict(
                    label="Nivel de prioridad",
                    values=df["prioridad_num"],
                    tickvals=list(PRIORIDAD_CODIGO.values()),
                    ticktext=list(PRIORIDAD_CODIGO.keys()),
                ),
                dict(label="Días abierto (máx. 2 años)", values=df["dias_abierto_cap"]),
                dict(label="Trimestre del aviso", values=df["Trimestre"], tickvals=[1, 2, 3, 4]),
            ],
        )
    )
    fig.update_layout(margin=dict(t=40, l=60, r=40, b=10), height=420)
    return fig