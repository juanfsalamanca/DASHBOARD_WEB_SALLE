"""Excel -> Parquet para arranque rápido."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data_loader import DATA_DIR, load_all  # noqa: E402


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    mortalidad, causas, dptos, mpios = load_all(use_cache=False)
    mortalidad.to_parquet(DATA_DIR / "mortalidad.parquet", index=False)
    causas.to_parquet(DATA_DIR / "causas.parquet", index=False)
    dptos.to_parquet(DATA_DIR / "dptos.parquet", index=False)
    mpios.to_parquet(DATA_DIR / "mpios.parquet", index=False)
    print(f"OK {len(mortalidad):,} filas -> data/*.parquet")


if __name__ == "__main__":
    main()
