import dash
from dash import html, dcc

dash.register_page(__name__, path="/", name="Inicio", icon="🏠")

layout = html.Div(
    [
        html.Div(
            [
                html.H1("Voltia S.A.S."),
                html.P(
                    "Contratista de mantenimiento e inspección de torres de energía para la "
                    "DEC (Distribuidora de Energía de Colombia). Gestionamos la atención de "
                    "avisos técnicos —vegetación, construcciones, obras, invasión y permisos "
                    "de ingreso— sobre la infraestructura de transmisión a nuestro cargo."
                ),
                html.Div(
                    [
                        html.Div(className="swatch", style={"background": "#12192B"}),
                        html.Div(className="swatch", style={"background": "#1CC9E8"}),
                        html.Div(className="swatch", style={"background": "#4A5568"}),
                        html.Div(className="swatch", style={"background": "#FFFFFF"})
                    ],
                    className="palette-row",
                ),
            ],
            className="hero",
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.H3("¿Qué encontrarás en este dashboard?"),
                        html.P(
                            "Dos tableros interactivos construidos a partir del histórico de "
                            "avisos y el catálogo de equipos/torres, con filtros, resaltado "
                            "visual y transiciones que permiten explorar el estado de la "
                            "operación en campo."
                        ),
                    ],
                    className="card card-full",
                ),
            ],
            className="content-grid",
        ),

        html.Div(
            [
                dcc.Link(
                    html.Div(
                        [
                            html.Div("📊", style={"fontSize": "26px"}),
                            html.H4("Tablero de Incidentes"),
                            html.P("Volumen, tipos y cumplimiento de tiempos de atención por zona."),
                        ],
                        className="board-link-card",
                    ),
                    href="/incidentes",
                ),
                dcc.Link(
                    html.Div(
                        [
                            html.Div("🔀", style={"fontSize": "26px"}),
                            html.H4("Tablero de Flujos y Relaciones"),
                            html.P("Cómo se distribuyen los avisos entre departamento, tipo y estado."),
                        ],
                        className="board-link-card",
                    ),
                    href="/flujos",
                ),
            ],
            className="board-links",
        ),
    ]
)
