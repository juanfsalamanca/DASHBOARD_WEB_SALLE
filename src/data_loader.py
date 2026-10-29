"""Carga Excel DANE / Divipola (con cache Parquet)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CATEGORIAS_EDAD = [
    ("Mortalidad neonatal", range(0, 5)),
    ("Mortalidad infantil", range(5, 7)),
    ("Primera infancia", range(7, 9)),
    ("Niñez", range(9, 11)),
    ("Adolescencia", range(11, 12)),
    ("Juventud", range(12, 14)),
    ("Adultez temprana", range(14, 17)),
    ("Adultez intermedia", range(17, 20)),
    ("Vejez", range(20, 25)),
    ("Longevidad / Centenarios", range(25, 29)),
    ("Edad desconocida", range(29, 30)),
]
ORDEN_EDAD = [c[0] for c in CATEGORIAS_EDAD]
MAPA_EDAD = {codigo: nombre for nombre, rng in CATEGORIAS_EDAD for codigo in rng}


def _resolve_file(patterns: list[str]) -> Path:
    for pattern in patterns:
        matches = sorted(DATA_DIR.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No se encontró ninguno de: {patterns} en {DATA_DIR}")


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized = {str(c).strip().upper().replace(" ", "_"): c for c in df.columns}
    for name in candidates:
        key = name.upper().replace(" ", "_")
        if key in normalized:
            return normalized[key]
    for key, original in normalized.items():
        for name in candidates:
            if name.upper().replace(" ", "_") in key:
                return original
    return None


def _require_column(df: pd.DataFrame, candidates: list[str], label: str) -> str:
    col = _find_column(df, candidates)
    if col is None:
        raise KeyError(f"Falta columna '{label}'. Disponibles: {list(df.columns)}")
    return col


def load_mortalidad(path: Path | None = None) -> pd.DataFrame:
    path = path or _resolve_file(["NoFetal2019.xlsx", "Anexo1*NoFetal*.xlsx", "*NoFetal*.xlsx"])
    xl = pd.ExcelFile(path, engine="openpyxl")
    sheet = "No_Fetales_2019" if "No_Fetales_2019" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    col_dpto = _require_column(df, ["COD_DEPARTAMENTO", "COD_DPTO", "CODIGO_DEPARTAMENTO", "DPTO"], "departamento")
    col_mpio = _require_column(df, ["COD_MUNICIPIO", "COD_MUNIC", "COD_MPIO", "CODIGO_MUNICIPIO"], "municipio")
    col_mes = _require_column(df, ["MES", "MES_MUERTE", "MES_DEF"], "mes")
    col_sexo = _require_column(df, ["SEXO", "SEXO_NAC"], "sexo")
    col_edad = _require_column(df, ["GRUPO_EDAD1", "GRUPO_EDAD", "EDAD_GRUPO"], "grupo edad")
    col_causa = _require_column(df, ["COD_MUERTE", "CAUSA_BASICA", "CAUSA", "COD_CAUSA", "C_BAS1"], "causa")

    out = pd.DataFrame(
        {
            "COD_DPTO": pd.to_numeric(df[col_dpto], errors="coerce").fillna(0).astype(int).astype(str).str.zfill(2),
            "COD_MPIO_RAW": pd.to_numeric(df[col_mpio], errors="coerce").fillna(0).astype(int).astype(str),
            "MES": pd.to_numeric(df[col_mes], errors="coerce"),
            "SEXO": pd.to_numeric(df[col_sexo], errors="coerce"),
            "GRUPO_EDAD1": pd.to_numeric(df[col_edad], errors="coerce"),
            "COD_MUERTE": df[col_causa].astype(str).str.strip().str.upper(),
        }
    )
    out["COD_MPIO"] = out["COD_DPTO"] + out["COD_MPIO_RAW"].str.zfill(3)
    out = out.drop(columns=["COD_MPIO_RAW"])
    out["SEXO_LABEL"] = out["SEXO"].map({1: "Hombre", 2: "Mujer"}).fillna("No informado")
    out["CATEGORIA_EDAD"] = out["GRUPO_EDAD1"].map(MAPA_EDAD).fillna("Edad desconocida")
    return out


def load_causas(path: Path | None = None) -> pd.DataFrame:
    path = path or _resolve_file(["CodigosDeMuerte.xlsx", "Anexo2*Codigo*.xlsx", "*Codigo*Muerte*.xlsx"])
    raw = pd.read_excel(path, sheet_name=0, header=None, engine="openpyxl")
    header_row = 8
    for i in range(min(20, len(raw))):
        row_txt = " ".join(str(v) for v in raw.iloc[i].tolist()).lower()
        if "cuatro caracteres" in row_txt:
            header_row = i
            break

    df = pd.read_excel(path, sheet_name=0, header=header_row, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)
    col_cod = _find_column(df, ["CÓDIGO DE LA CIE-10 CUATRO CARACTERES", "CODIGO DE LA CIE-10 CUATRO CARACTERES", "CODIGO"])
    col_nom = _find_column(df, ["DESCRIPCION  DE CÓDIGOS MORTALIDAD A CUATRO CARACTERES", "DESCRIPCION", "NOMBRE"])
    if col_cod is None or col_nom is None:
        col_cod, col_nom = cols[4], cols[5]

    out = pd.DataFrame(
        {
            "COD_MUERTE": df[col_cod].astype(str).str.strip().str.upper(),
            "NOMBRE_CAUSA": df[col_nom].astype(str).str.strip(),
        }
    )
    if len(cols) >= 4:
        tres = pd.DataFrame(
            {
                "COD_MUERTE": df[cols[2]].astype(str).str.strip().str.upper(),
                "NOMBRE_CAUSA": df[cols[3]].astype(str).str.strip(),
            }
        )
        out = pd.concat([out, tres], ignore_index=True)
    out = out[out["COD_MUERTE"].str.match(r"^[A-Z]\d", na=False)]
    return out.drop_duplicates(subset=["COD_MUERTE"])


def load_divipola(path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = path or _resolve_file(["Divipola.xlsx", "Divipola*.xlsx", "*Divipola*.xlsx"])
    df = pd.read_excel(path, sheet_name=0, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    col_cod_dpto = _require_column(df, ["COD_DEPARTAMENTO", "CODIGO_DEPARTAMENTO", "COD_DPTO"], "código dpto")
    col_nom_dpto = _require_column(df, ["DEPARTAMENTO", "NOMBRE_DEPARTAMENTO", "NOM_DPTO"], "nombre dpto")
    col_cod_mpio = _require_column(df, ["COD_MUNICIPIO", "CODIGO_MUNICIPIO", "COD_MPIO"], "código mpio")
    col_nom_mpio = _require_column(df, ["MUNICIPIO", "NOMBRE_MUNICIPIO", "NOM_MPIO"], "nombre mpio")

    out = pd.DataFrame(
        {
            "COD_DPTO": pd.to_numeric(df[col_cod_dpto], errors="coerce").fillna(0).astype(int).astype(str).str.zfill(2),
            "NOM_DPTO": df[col_nom_dpto].astype(str).str.strip().str.title(),
            "COD_MPIO_RAW": pd.to_numeric(df[col_cod_mpio], errors="coerce").fillna(0).astype(int).astype(str),
            "NOM_MPIO": df[col_nom_mpio].astype(str).str.strip().str.title(),
        }
    )
    out["COD_MPIO"] = out["COD_DPTO"] + out["COD_MPIO_RAW"].str.zfill(3)
    out = out.drop(columns=["COD_MPIO_RAW"])
    dptos = out[["COD_DPTO", "NOM_DPTO"]].drop_duplicates()
    mpios = out[["COD_DPTO", "COD_MPIO", "NOM_MPIO", "NOM_DPTO"]].drop_duplicates(subset=["COD_MPIO"])
    return dptos, mpios


def load_all(use_cache: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = {
        "mortalidad": DATA_DIR / "mortalidad.parquet",
        "causas": DATA_DIR / "causas.parquet",
        "dptos": DATA_DIR / "dptos.parquet",
        "mpios": DATA_DIR / "mpios.parquet",
    }
    if use_cache and all(p.exists() for p in paths.values()):
        return (
            pd.read_parquet(paths["mortalidad"]),
            pd.read_parquet(paths["causas"]),
            pd.read_parquet(paths["dptos"]),
            pd.read_parquet(paths["mpios"]),
        )

    mortalidad = load_mortalidad()
    causas = load_causas()
    dptos, mpios = load_divipola()
    mortalidad = mortalidad.merge(dptos, on="COD_DPTO", how="left")
    mortalidad = mortalidad.merge(mpios[["COD_MPIO", "NOM_MPIO"]], on="COD_MPIO", how="left")
    mortalidad["NOM_DPTO"] = mortalidad["NOM_DPTO"].fillna("Desconocido")
    mortalidad["NOM_MPIO"] = mortalidad["NOM_MPIO"].fillna("Desconocido")
    return mortalidad, causas, dptos, mpios
