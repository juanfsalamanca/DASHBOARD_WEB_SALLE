"""Dashboard Dash — Mortalidad Colombia 2019."""

from __future__ import annotations

import os
import traceback

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback_context, dash_table, dcc, html, no_update
from plotly import graph_objects as go

from src.charts import (
    fig_barras_sexo_dpto,
    fig_barras_violentas,
    fig_circular_menor_mortalidad,
    fig_histograma_edad,
    fig_lineas_mes,
    fig_mapa_departamentos,
)
from src.data_loader import load_all
from src.processing import (
    histograma_edad,
    muertes_por_departamento,
    muertes_por_mes,
    muertes_por_sexo_departamento,
    top10_causas,
    top10_ciudades_menor_mortalidad,
    top5_ciudades_violentas,
)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="Mortalidad Colombia 2019",
)
server = app.server

print("Preparando dashboard...")
try:
    DF, CAUSAS, _, _ = load_all()
    LOAD_ERROR = None
except Exception as exc:  # noqa: BLE001
    DF, CAUSAS = None, None
    LOAD_ERROR = f"{exc}\n\n{traceback.format_exc()}"
print("Listo." if LOAD_ERROR is None else "Error de datos.")


def _filter_df(dpto: str | None, sexo: str | None) -> pd.DataFrame:
    data = DF
    if dpto and dpto != "TODOS":
        data = data[data["NOM_DPTO"] == dpto]
    if sexo and sexo != "TODOS":
        data = data[data["SEXO_LABEL"] == sexo]
    return data


def _kpi_cards(data: pd.DataFrame) -> list:
    items = [
        ("Muertes (filtro)", f"{len(data):,}".replace(",", "."), "Registros visibles"),
        ("Departamentos", str(data["NOM_DPTO"].nunique()), "En la selección"),
        ("Municipios", str(data["NOM_MPIO"].nunique()), "Con al menos 1 muerte"),
        (
            "Homicidios X95",
            f"{int(data['COD_MUERTE'].astype(str).str.startswith('X95', na=False).sum()):,}".replace(",", "."),
            "Arma de fuego",
        ),
    ]
    return [
        dbc.Col(
            html.Div(
                [html.H6(t), html.H3(v, className="kpi-value"), html.Div(s, className="kpi-sub")],
                className="kpi-card card-body",
            ),
            md=6,
            lg=3,
            className="mb-3",
        )
        for t, v, s in items
    ]


def _section(title: str, tag: str, body, class_name: str = "mb-4") -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader([html.Span(title), html.Span(tag, className="section-tag")]),
            dbc.CardBody(body),
        ],
        className=f"section-card {class_name}",
    )


def _empty_fig(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.65)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        uirevision=msg,
    )
    return fig


def _tabla_causas(df_causas: pd.DataFrame):
    return dash_table.DataTable(
        columns=[
            {"name": "Código", "id": "COD_MUERTE"},
            {"name": "Nombre de la causa", "id": "NOMBRE"},
            {"name": "Total de casos", "id": "TOTAL_CASOS"},
        ],
        data=df_causas.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#0E7490",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "left",
        },
        style_cell={
            "padding": "12px",
            "textAlign": "left",
            "fontFamily": "IBM Plex Sans, Segoe UI, sans-serif",
            "backgroundColor": "rgba(255,255,255,0.9)",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#ECFEFF"},
            {"if": {"state": "active"}, "backgroundColor": "#CFFAFE", "border": "1px solid #0E7490"},
        ],
        page_size=10,
    )


def build_layout():
    if LOAD_ERROR:
        return dbc.Container(
            [
                html.H2("No se pudieron cargar los datos", className="text-danger mt-4"),
                html.Pre(LOAD_ERROR, className="bg-light p-3 border"),
            ],
            fluid=True,
        )

    dpto_opts = [{"label": "Todos los departamentos", "value": "TODOS"}] + [
        {"label": d, "value": d} for d in sorted(DF["NOM_DPTO"].dropna().unique())
    ]
    sexo_opts = [
        {"label": "Todos", "value": "TODOS"},
        {"label": "Hombre", "value": "Hombre"},
        {"label": "Mujer", "value": "Mujer"},
    ]

    return html.Div(
        [
            html.Div(className="bg-stage"),
            html.Div(className="orb orb-a"),
            html.Div(className="orb orb-b"),
            html.Div(className="orb orb-c"),
            dbc.Container(
                [
                    html.Div(
                        [
                            html.Span("EEVV · DANE 2019", className="hero-badge"),
                            html.H1("Mortalidad en Colombia"),
                            html.P(
                                "Filtra por departamento o sexo. Clic en el mapa o en una barra para filtrar; "
                                "otro clic en el mismo vuelve a todos. Usa Limpiar filtros para resetear.",
                                className="lead",
                            ),
                        ],
                        className="hero",
                    ),
                    html.Div(
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Departamento"),
                                        html.Div(
                                            dcc.Dropdown(
                                                id="filtro-dpto",
                                                options=dpto_opts,
                                                value="TODOS",
                                                clearable=False,
                                                searchable=True,
                                                maxHeight=280,
                                            ),
                                            className="filter-dropdown-wrap",
                                        ),
                                    ],
                                    md=5,
                                    className="filter-col",
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Sexo"),
                                        html.Div(
                                            dcc.Dropdown(
                                                id="filtro-sexo",
                                                options=sexo_opts,
                                                value="TODOS",
                                                clearable=False,
                                                maxHeight=280,
                                            ),
                                            className="filter-dropdown-wrap",
                                        ),
                                    ],
                                    md=4,
                                    className="filter-col",
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Acciones"),
                                        dbc.Button(
                                            "Limpiar filtros",
                                            id="btn-limpiar",
                                            color="warning",
                                            className="w-100",
                                            outline=True,
                                        ),
                                    ],
                                    md=3,
                                ),
                            ],
                            className="g-3",
                        ),
                        className="filters-panel",
                    ),
                    html.Div(id="filter-banner", className="filter-banner"),
                    html.Div(dbc.Row(id="kpi-row", className="g-3"), className="kpi-grid mb-4"),
                    html.Div(
                        [
                            _section(
                                "1. Mapa — muertes por departamento",
                                "Clic / otro clic = volver",
                                dcc.Graph(id="graph-mapa", config={"displayModeBar": True, "responsive": True}),
                            ),
                            _section(
                                "2. Líneas — muertes por mes",
                                "Según filtro",
                                dcc.Graph(id="graph-mes", config={"displayModeBar": False}),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        _section(
                                            "3. Top 5 ciudades violentas (X95)",
                                            "Según filtro",
                                            dcc.Graph(id="graph-violentas"),
                                            class_name="h-100",
                                        ),
                                        lg=6,
                                        className="mb-4",
                                    ),
                                    dbc.Col(
                                        _section(
                                            "4. Circular — menor mortalidad",
                                            "Según filtro",
                                            dcc.Graph(id="graph-circular"),
                                            class_name="h-100",
                                        ),
                                        lg=6,
                                        className="mb-4",
                                    ),
                                ]
                            ),
                            _section(
                                "5. Tabla — 10 principales causas",
                                "Según filtro",
                                html.Div(id="tabla-causas"),
                            ),
                            _section(
                                "6. Barras apiladas — sexo por departamento",
                                "Clic / otro clic = volver",
                                dcc.Graph(id="graph-sexo", style={"height": "560px"}),
                            ),
                            _section(
                                "7. Histograma — grupos de edad",
                                "Según filtro",
                                dcc.Graph(id="graph-edad"),
                            ),
                        ],
                        className="charts-stack",
                    ),
                    html.Footer(
                        html.P(
                            "Fuente: DANE — EEVV 2019 · Defunciones no fetales · Dash + Plotly",
                            className="footer-note small",
                        )
                    ),
                ],
                fluid=True,
                className="px-3 px-lg-4 app-shell",
            ),
        ]
    )


app.layout = build_layout()


def _nombre_desde_click(punto: dict) -> str | None:
    custom = punto.get("customdata")
    if custom is not None:
        if isinstance(custom, (list, tuple)):
            return str(custom[0]) if custom[0] is not None else None
        return str(custom)
    if punto.get("location"):
        codigo = str(punto["location"]).zfill(2)
        match = DF.loc[DF["COD_DPTO"] == codigo, "NOM_DPTO"]
        return str(match.iloc[0]) if len(match) else None
    if punto.get("x"):
        return str(punto["x"])
    return None


@app.callback(
    Output("filtro-dpto", "value"),
    Output("filtro-sexo", "value"),
    Input("btn-limpiar", "n_clicks"),
    Input("graph-mapa", "clickData"),
    Input("graph-sexo", "clickData"),
    State("filtro-dpto", "value"),
    State("filtro-sexo", "value"),
    prevent_initial_call=True,
)
def sync_filters(_n, click_mapa, click_sexo, dpto_actual, sexo_actual):
    triggered = callback_context.triggered[0]["prop_id"] if callback_context.triggered else ""
    sexo_actual = sexo_actual or "TODOS"
    dpto_actual = dpto_actual or "TODOS"

    if triggered.startswith("btn-limpiar"):
        return "TODOS", "TODOS"

    if triggered.startswith("graph-mapa") and click_mapa:
        nombre = _nombre_desde_click(click_mapa["points"][0])
        if not nombre:
            return no_update, no_update
        if dpto_actual == nombre:
            return "TODOS", sexo_actual
        return nombre, sexo_actual

    if triggered.startswith("graph-sexo") and click_sexo:
        nombre = _nombre_desde_click(click_sexo["points"][0])
        if not nombre:
            return no_update, no_update
        # Volver: segundo clic en el mismo departamento
        if dpto_actual == nombre:
            return "TODOS", "TODOS"
        # Al elegir por barra, resetea sexo para no quedar atrapado en Hombre/Mujer
        return nombre, "TODOS"

    return no_update, no_update


@app.callback(
    Output("filter-banner", "children"),
    Output("filter-banner", "className"),
    Output("kpi-row", "children"),
    Output("graph-mapa", "figure"),
    Output("graph-mes", "figure"),
    Output("graph-violentas", "figure"),
    Output("graph-circular", "figure"),
    Output("tabla-causas", "children"),
    Output("graph-sexo", "figure"),
    Output("graph-edad", "figure"),
    Input("filtro-dpto", "value"),
    Input("filtro-sexo", "value"),
)
def refresh_dashboard(dpto, sexo):
    dpto = dpto or "TODOS"
    sexo = sexo or "TODOS"
    data = _filter_df(dpto, sexo)

    partes = []
    if dpto != "TODOS":
        partes.append(f"Departamento: {dpto}")
    if sexo != "TODOS":
        partes.append(f"Sexo: {sexo}")
    activo = bool(partes)
    banner_children = [
        html.Div(
            [
                html.Span(" · ".join(partes) if partes else ""),
                html.Span(
                    "Clic de nuevo en la misma barra/mapa o Limpiar filtros para volver",
                    className="small",
                ),
                html.Span(f"{len(data):,} registros".replace(",", ".")),
            ],
            className="d-flex w-100 justify-content-between gap-3 flex-wrap align-items-center",
        )
    ]
    banner_class = "filter-banner visible" if activo else "filter-banner"
    selected = None if dpto == "TODOS" else dpto
    fig_mapa = fig_mapa_departamentos(muertes_por_departamento(DF), selected=selected)

    # Barras de sexo: SIEMPRE nacional para poder cambiar/volver con clic
    fig_sexo = fig_barras_sexo_dpto(muertes_por_sexo_departamento(DF))

    if data.empty:
        vacio = _empty_fig("Sin datos para este filtro")
        return (
            banner_children,
            banner_class,
            _kpi_cards(data),
            fig_mapa,
            vacio,
            vacio,
            vacio,
            html.P("Sin registros.", className="text-muted m-0"),
            fig_sexo,
            vacio,
        )

    return (
        banner_children,
        banner_class,
        _kpi_cards(data),
        fig_mapa,
        fig_lineas_mes(muertes_por_mes(data)),
        fig_barras_violentas(top5_ciudades_violentas(data)),
        fig_circular_menor_mortalidad(top10_ciudades_menor_mortalidad(data)),
        _tabla_causas(top10_causas(data, CAUSAS)),
        fig_sexo,
        fig_histograma_edad(histograma_edad(data)),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DASH_DEBUG", "0") == "1")
