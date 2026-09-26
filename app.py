"""
ElectroVigía S.A.S. — Dashboard de incidentes y equipos en torres de energía
Grupo 1: Barras agrupadas/divergentes (básico) + Coordenadas paralelas y Sankey (otros)

Autoras: Andrea Katerin Cruz Padilla · Ivon Daniela Sepúlveda Pérez
"""

import dash
from dash import Dash, html, dcc, Input, Output, State

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="ElectroVigía | Dashboard de incidentes",
)
server = app.server  # <- lo necesita gunicorn para producción (Render)


def nav_links():
    items = []
    for page in dash.page_registry.values():
        items.append(
            html.Div(
                dcc.Link(
                    [html.Span(page.get("icon", "•") + "  "), html.Span(page["name"], className="label")],
                    href=page["relative_path"],
                    className="nav-link",
                    id={"type": "nav-link", "index": page["relative_path"]},
                )
            )
        )
    return items


app.layout = html.Div(
    [
        dcc.Location(id="url"),

        # Header solo visible en móvil
        html.Div(
            [
                html.Button("☰", id="menu-button", className="menu-button"),
                html.Div("ElectroVigía", style={"fontWeight": "700"}),
                html.Div(style={"width": "24px"}),  # espaciador
            ],
            className="mobile-header",
        ),

        # Overlay que cierra el menú en móvil
        html.Div(id="overlay", className="overlay"),

        # Sidebar
        html.Div(
            [
                html.Div(
                    [
                        html.Div("EV", className="logo-mark"),
                        html.Div(
                            [
                                html.Div("ElectroVigía", className="brand-name"),
                                html.Div("Contratista DEC", className="brand-sub"),
                            ]
                        ),
                    ],
                    className="logo-box",
                ),
                html.Div(nav_links()),
            ],
            id="sidebar",
            className="sidebar",
        ),

        # Contenido de cada página
        html.Div(dash.page_container, className="main-content"),
    ]
)


# ---- Interacción: abrir / cerrar el menú lateral en móvil ----
@app.callback(
    Output("sidebar", "className"),
    Output("overlay", "className"),
    Input("menu-button", "n_clicks"),
    Input("overlay", "n_clicks"),
    State("sidebar", "className"),
    prevent_initial_call=True,
)
def toggle_sidebar(menu_clicks, overlay_clicks, current_class):
    if current_class and "open" in current_class:
        return "sidebar", "overlay"
    return "sidebar open", "overlay visible"


if __name__ == "__main__":
    # host='0.0.0.0' para poder verlo desde el celular en la misma red (ver guía)
    app.run(debug=True, host="0.0.0.0", port=8050)
