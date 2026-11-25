# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openpyxl>=3.1",
#   "pandas>=2.2",
#   "pyarrow>=17.0",
# ]
# ///
"""Build the MINSA epi-week calendar (2018-2026) and cache CDC Observatorio pilot rows."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MAIN_DATA = Path("/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data")
OBS_DIR = MAIN_DATA / "archive-staging/observatorio/20261123T161922Z"
PROTO = MAIN_DATA / "prototypes/climate-district-week"


def minsa_epiweek(d: pd.Timestamp) -> tuple[int, int]:
    """Return (epi_year, epi_week) in MINSA's Sunday-Saturday calendar (week 1 contains 4 Jan)."""

    def week1_start(y: int) -> pd.Timestamp:
        jan4 = pd.Timestamp(year=y, month=1, day=4)
        return jan4 - pd.Timedelta(days=(jan4.day_of_week + 1) % 7)

    y = d.year
    if d >= week1_start(y + 1):
        return y + 1, 1
    s_cur = week1_start(y)
    if d >= s_cur:
        return y, int((d - s_cur).days // 7) + 1
    s_prev = week1_start(y - 1)
    return y - 1, int((d - s_prev).days // 7) + 1


def main() -> None:
    PROTO.mkdir(parents=True, exist_ok=True)

    # 1. MINSA epi-week calendar
    dates = pd.date_range("2017-12-31", "2026-11-25", freq="D")
    ews = [minsa_epiweek(d) for d in dates]
    cal = pd.DataFrame(
        {
            "date": dates,
            "epi_year": [x[0] for x in ews],
            "epi_week": [x[1] for x in ews],
        }
    )
    cal.to_parquet(PROTO / "minsa_calendar.parquet", index=False)

    # 2. Observatorio pilot (confirmado sheet; climate columns repeat across case classes)
    parts = []
    for dep in ("piura", "tumbes", "lambayeque"):
        df = pd.read_excel(
            OBS_DIR / f"observatorio_20261123T161922Z_{dep}_confirmado.xlsx",
            sheet_name="Distrito",
        )
        parts.append(df)
    obs = pd.concat(parts, ignore_index=True)
    obs["ubigeo"] = obs["UBIGEO"].astype(str).str.zfill(6)
    obs = obs.rename(columns={"Ano": "epi_year", "Semana": "epi_week"})
    # Drop padded weeks after the page's cut (2026-SE45)
    obs = obs[
        (obs["epi_year"] < 2026) | ((obs["epi_year"] == 2026) & (obs["epi_week"] <= 45))
    ].copy()
    obs.to_parquet(PROTO / "observatorio_pilot.parquet", index=False)
    print(f"Saved minsa_calendar.parquet ({len(cal)} days) and observatorio_pilot.parquet ({len(obs)} rows)")


if __name__ == "__main__":
    main()
