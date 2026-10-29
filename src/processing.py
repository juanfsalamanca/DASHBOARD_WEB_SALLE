"""Agregaciones para las visualizaciones."""

from __future__ import annotations

import pandas as pd

from .data_loader import ORDEN_EDAD


def muertes_por_departamento(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["COD_DPTO", "NOM_DPTO"], as_index=False)
        .size()
        .rename(columns={"size": "TOTAL_MUERTES"})
        .sort_values("TOTAL_MUERTES", ascending=False)
    )


def muertes_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    meses = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
    }
    g = (
        df.dropna(subset=["MES"])
        .groupby("MES", as_index=False)
        .size()
        .rename(columns={"size": "TOTAL_MUERTES"})
    )
    g["MES"] = g["MES"].astype(int)
    g = g[g["MES"].between(1, 12)].sort_values("MES")
    g["MES_NOM"] = g["MES"].map(meses)
    return g


def top5_ciudades_violentas(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["COD_MUERTE"].str.startswith("X95", na=False)
    g = (
        df.loc[mask]
        .groupby(["COD_MPIO", "NOM_MPIO", "NOM_DPTO"], as_index=False)
        .size()
        .rename(columns={"size": "HOMICIDIOS_X95"})
        .sort_values("HOMICIDIOS_X95", ascending=False)
        .head(5)
    )
    g["CIUDAD"] = g["NOM_MPIO"] + " (" + g["NOM_DPTO"] + ")"
    return g


def top10_ciudades_menor_mortalidad(df: pd.DataFrame, min_registros: int = 1) -> pd.DataFrame:
    g = (
        df.groupby(["COD_MPIO", "NOM_MPIO", "NOM_DPTO"], as_index=False)
        .size()
        .rename(columns={"size": "TOTAL_MUERTES"})
    )
    g = g[g["TOTAL_MUERTES"] >= min_registros]
    g = g.sort_values(["TOTAL_MUERTES", "NOM_MPIO"], ascending=[True, True]).head(10)
    g["CIUDAD"] = g["NOM_MPIO"] + " (" + g["NOM_DPTO"] + ")"
    return g


def top10_causas(df: pd.DataFrame, causas: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby("COD_MUERTE", as_index=False)
        .size()
        .rename(columns={"size": "TOTAL_CASOS"})
        .sort_values("TOTAL_CASOS", ascending=False)
        .head(10)
    )
    causas_idx = causas.set_index("COD_MUERTE")["NOMBRE_CAUSA"].to_dict()

    def resolver_nombre(codigo: str) -> str:
        codigo = str(codigo).upper().strip()
        if codigo in causas_idx:
            return causas_idx[codigo]
        for n in (4, 3):
            if len(codigo) >= n and codigo[:n] in causas_idx:
                return causas_idx[codigo[:n]]
        return "Sin descripción"

    g["NOMBRE"] = g["COD_MUERTE"].map(resolver_nombre)
    return g[["COD_MUERTE", "NOMBRE", "TOTAL_CASOS"]]


def muertes_por_sexo_departamento(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["NOM_DPTO", "SEXO_LABEL"], as_index=False)
        .size()
        .rename(columns={"size": "TOTAL_MUERTES"})
    )


def histograma_edad(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby("CATEGORIA_EDAD", as_index=False)
        .size()
        .rename(columns={"size": "TOTAL_MUERTES"})
    )
    g["CATEGORIA_EDAD"] = pd.Categorical(g["CATEGORIA_EDAD"], categories=ORDEN_EDAD, ordered=True)
    return g.sort_values("CATEGORIA_EDAD")
