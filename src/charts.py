"""Figuras Plotly del dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

GEOJSON_PATH = Path(__file__).resolve().parent.parent / "assets" / "colombia_departamentos.geojson"
_GEOJSON_CACHE: dict | None = None

COLOR_PRIMARY = "#0E7490"
COLOR_MEN = "#0284C7"
COLOR_WOMEN = "#E11D48"
PALETTE = [
    "#0E7490", "#14B8A6", "#F59E0B", "#8B5CF6", "#0369A1",
    "#059669", "#D97706", "#64748B", "#EC4899", "#22C55E",
]


def _load_geojson() -> dict:
    global _GEOJSON_CACHE
    if _GEOJSON_CACHE is not None:
        return _GEOJSON_CACHE
    if GEOJSON_PATH.exists():
        _GEOJSON_CACHE = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    else:
        _GEOJSON_CACHE = {"type": "FeatureCollection", "features": []}
    return _GEOJSON_CACHE


def _base_layout(fig: go.Figure, height: int | None = None, uirevision: str = "mort-2019") -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.65)",
        font=dict(family="Segoe UI, Trebuchet MS, sans-serif", color="#0F172A"),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Segoe UI"),
        margin=dict(l=20, r=20, t=60, b=40),
        height=height,
        uirevision=uirevision,
    )
    return fig


def fig_mapa_departamentos(df_dpto: pd.DataFrame, selected: str | None = None) -> go.Figure:
    geojson = _load_geojson()
    data = df_dpto.copy()
    data["COD_DPTO"] = data["COD_DPTO"].astype(str).str.zfill(2)
    if selected:
        data["COLOR_MAPA"] = data.apply(
            lambda r: r["TOTAL_MUERTES"] if r["NOM_DPTO"] == selected else 0,
            axis=1,
        )
        titulo = f"Mapa — foco en {selected} (otro clic vuelve a todos)"
    else:
        data["COLOR_MAPA"] = data["TOTAL_MUERTES"]
        titulo = "Mapa — clic en un departamento para filtrar"

    fig = px.choropleth(
        data,
        geojson=geojson,
        locations="COD_DPTO",
        featureidkey="properties.DPTO",
        color="COLOR_MAPA",
        hover_name="NOM_DPTO",
        custom_data=["NOM_DPTO", "TOTAL_MUERTES"],
        color_continuous_scale="Tealgrn",
        labels={"COLOR_MAPA": "Total muertes"},
        title=titulo,
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Muertes: %{customdata[1]:,}<extra>Clic</extra>",
        marker_line_width=1.2 if selected else 0.6,
        marker_line_color="#F59E0B" if selected else "#134E4A",
    )
    if selected:
        fig.add_annotation(
            text=f"Filtro: {selected} · clic de nuevo para volver",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.01,
            showarrow=False,
            bgcolor="rgba(14,116,144,0.95)",
            font=dict(color="white", size=13),
            borderpad=8,
        )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)", projection_type="mercator")
    return _base_layout(fig, height=520, uirevision=f"mapa-{selected or 'TODOS'}")


def fig_lineas_mes(df_mes: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_mes["MES_NOM"],
            y=df_mes["TOTAL_MUERTES"],
            mode="lines+markers",
            name="Muertes",
            line=dict(color=COLOR_PRIMARY, width=4, shape="spline"),
            marker=dict(size=12, color="#F59E0B", line=dict(width=2, color="white")),
            fill="tozeroy",
            fillcolor="rgba(14,116,144,0.18)",
            hovertemplate="<b>%{x}</b><br>Muertes: %{y:,}<extra></extra>",
        )
    )
    if len(df_mes):
        peak = df_mes.loc[df_mes["TOTAL_MUERTES"].idxmax()]
        fig.add_annotation(
            x=peak["MES_NOM"],
            y=peak["TOTAL_MUERTES"],
            text=f"Pico: {int(peak['TOTAL_MUERTES']):,}",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            bgcolor="#0E7490",
            font=dict(color="white"),
        )
    fig.update_layout(
        title="Muertes por mes",
        xaxis_title="Mes",
        yaxis_title="Total de muertes",
        xaxis=dict(categoryorder="array", categoryarray=list(df_mes["MES_NOM"])),
        yaxis_gridcolor="#E2E8F0",
    )
    rev = f"mes-{int(df_mes['TOTAL_MUERTES'].sum()) if len(df_mes) else 0}"
    return _base_layout(fig, height=420, uirevision=rev)


def fig_barras_violentas(df_top5: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df_top5,
        x="HOMICIDIOS_X95",
        y="CIUDAD",
        orientation="h",
        title="Top 5 ciudades más violentas (X95)",
        labels={"HOMICIDIOS_X95": "Homicidios (X95)", "CIUDAD": "Ciudad"},
        color="HOMICIDIOS_X95",
        color_continuous_scale="Turbo",
        text="HOMICIDIOS_X95",
        custom_data=["NOM_MPIO", "NOM_DPTO"],
    )
    fig.update_traces(
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>X95: %{x:,}<extra></extra>",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
    rev = f"viol-{int(df_top5['HOMICIDIOS_X95'].sum()) if len(df_top5) else 0}"
    return _base_layout(fig, height=420, uirevision=rev)


def fig_circular_menor_mortalidad(df_top10: pd.DataFrame) -> go.Figure:
    fig = px.pie(
        df_top10,
        names="CIUDAD",
        values="TOTAL_MUERTES",
        title="10 municipios con menor mortalidad",
        color_discrete_sequence=PALETTE,
        hole=0.42,
    )
    fig.update_traces(textposition="inside", textinfo="label+value", pull=[0.08] + [0] * max(0, len(df_top10) - 1))
    fig.update_layout(legend_title_text="Municipio")
    rev = f"pie-{int(df_top10['TOTAL_MUERTES'].sum()) if len(df_top10) else 0}-{len(df_top10)}"
    return _base_layout(fig, height=420, uirevision=rev)


def fig_barras_sexo_dpto(df_sexo: pd.DataFrame) -> go.Figure:
    orden = (
        df_sexo.groupby("NOM_DPTO")["TOTAL_MUERTES"].sum().sort_values(ascending=False).index.tolist()
    )
    fig = px.bar(
        df_sexo,
        x="NOM_DPTO",
        y="TOTAL_MUERTES",
        color="SEXO_LABEL",
        title="Muertes por sexo y departamento — clic en barra (otro clic vuelve)",
        labels={"NOM_DPTO": "Departamento", "TOTAL_MUERTES": "Total de muertes", "SEXO_LABEL": "Sexo"},
        color_discrete_map={"Hombre": COLOR_MEN, "Mujer": COLOR_WOMEN, "No informado": "#94A3B8"},
        category_orders={"NOM_DPTO": orden, "SEXO_LABEL": ["Hombre", "Mujer", "No informado"]},
        custom_data=["NOM_DPTO", "SEXO_LABEL"],
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}: %{y:,}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-45,
        legend_title_text="Sexo",
        margin=dict(b=120),
        yaxis_gridcolor="#E2E8F0",
    )
    rev = f"sexo-{int(df_sexo['TOTAL_MUERTES'].sum()) if len(df_sexo) else 0}"
    return _base_layout(fig, height=560, uirevision=rev)


def fig_histograma_edad(df_edad: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df_edad,
        x="CATEGORIA_EDAD",
        y="TOTAL_MUERTES",
        title="Distribución por grupo de edad",
        labels={"CATEGORIA_EDAD": "Grupo de edad", "TOTAL_MUERTES": "Total de muertes"},
        color="TOTAL_MUERTES",
        color_continuous_scale="Viridis",
        text="TOTAL_MUERTES",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_tickangle=-28, coloraxis_showscale=False, margin=dict(b=140), yaxis_gridcolor="#E2E8F0")
    rev = f"edad-{int(df_edad['TOTAL_MUERTES'].sum()) if len(df_edad) else 0}"
    return _base_layout(fig, height=460, uirevision=rev)
