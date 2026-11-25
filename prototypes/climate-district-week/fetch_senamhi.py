# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.2",
#   "pyarrow>=17.0",
#   "requests>=2.32",
# ]
# ///
"""Fetch daily observations (2018-2026) for selected pilot SENAMHI stations.

Uses the public SENAMHI Observatorio JSON API discovered from
https://observatorio.senamhi.gob.pe/investigadores/datos:
  GET https://servicios.senamhi.gob.pe/api/station/stations/{id}/periods
  GET https://servicios.senamhi.gob.pe/api/station/stations/{id}/readings?period=YYYYMM

No login or CAPTCHA is required. Requests are serialized with a polite pause.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(
    "/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week"
)
OUT_DIR = DATA_DIR / "senamhi"
API = "https://servicios.senamhi.gob.pe/api"

# Representative pilot stations spanning main cities, coastal ocean-masked
# districts (Tumbes, La Cruz, Zarumilla, Colan/Paita, Lambayeque, Reque),
# and Andean elevation stress tests (Ayabaca, Huancabamba).
STATIONS = [
    ("105063", "SAN MIGUEL", "200105", "Piura urban/valley"),
    ("105100", "MIRAFLORES", "200104", "Piura city (Castilla)"),
    ("103038", "PUERTO PIZARRO", "240101", "Tumbes coastal (land_frac=0.52)"),
    ("100072", "LA CRUZ", "240103", "Tumbes coastal (land_frac=0.78)"),
    ("103041", "EL SALTO", "240301", "Zarumilla coastal (land_frac=0.61)"),
    ("104090", "LA ESPERANZA", "200504", "Colan/Paita coastal (land_frac=0.78)"),
    ("106108", "LAMBAYEQUE", "140301", "Lambayeque coastal/city (land_frac=0.95)"),
    ("106046", "REQUE", "140113", "Chiclayo metro south (0 cell centers)"),
    ("104058", "AYABACA", "200201", "Piura Andean stress test (2648 m)"),
    ("105055", "HUANCABAMBA", "200301", "Piura Andean stress test (1959 m)"),
]


def fetch_json(session: requests.Session, url: str, params: dict | None = None) -> dict:
    for attempt in range(4):
        try:
            r = session.get(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Goberlab-dengue-data-pipeline-prototype/0.1"})

    actives = json.loads((DATA_DIR / "senamhi_actives.json").read_text())["data"]
    meta_by_id = {str(r["stationId"]): r for r in actives}

    all_rows: list[dict] = []
    meta_rows: list[dict] = []

    for sid, name, ubigeo, role in STATIONS:
        cache_path = OUT_DIR / f"station_{sid}.parquet"
        m = meta_by_id.get(sid, {})
        meta_rows.append(
            {
                "station_id": sid,
                "legacy_id": m.get("legacyStationId"),
                "name": m.get("name", name),
                "ubigeo": ubigeo,
                "role": role,
                "latitude": float(m["latitude"]) if m.get("latitude") else None,
                "longitude": float(m["longitude"]) if m.get("longitude") else None,
                "altitude_m": float(m["altitude"]) if m.get("altitude") is not None else None,
                "sub_type": m.get("subTypeDescription"),
                "category": m.get("categoryAbbreviation"),
            }
        )

        if cache_path.exists():
            df_st = pd.read_parquet(cache_path)
            print(f"[cached] {sid} {name}: {len(df_st)} daily rows")
            all_rows.extend(df_st.to_dict("records"))
            continue

        per_resp = fetch_json(session, f"{API}/station/stations/{sid}/periods")
        periods = sorted(
            str(p["id"]) for p in (per_resp.get("data") or []) if str(p["id"]) >= "201801"
        )
        print(f"Fetching {sid} {name} ({len(periods)} months: {periods[0]}..{periods[-1]})")

        st_rows: list[dict] = []
        for ym in periods:
            resp = fetch_json(
                session, f"{API}/station/stations/{sid}/readings", params={"period": ym}
            )
            data = resp.get("data") or {}
            for rec in data.get("readings") or []:
                row = {"station_id": sid, "ubigeo": ubigeo, "date": rec.get("date")}
                for v in rec.get("values") or []:
                    col = v.get("column")
                    val = v.get("value")
                    if col in (
                        "TEMPERATURA_MAXIMA",
                        "TEMPERATURA_MINIMA",
                        "HUMEDAD_RELATIVA",
                        "PRECIPITACION",
                        "TEMPERATURA",
                    ):
                        try:
                            row[col] = float(val) if val is not None else None
                        except (TypeError, ValueError):
                            row[col] = None
                st_rows.append(row)
            time.sleep(0.15)

        df_st = pd.DataFrame(st_rows)
        if not df_st.empty:
            df_st = df_st.drop_duplicates(subset=["station_id", "date"]).sort_values("date")
            df_st.to_parquet(cache_path, index=False)
            print(f"  -> saved {len(df_st)} rows to {cache_path.name}")
            all_rows.extend(df_st.to_dict("records"))

    pd.DataFrame(meta_rows).to_parquet(OUT_DIR / "stations_meta.parquet", index=False)
    df_all = pd.DataFrame(all_rows)
    df_all.to_parquet(OUT_DIR / "pilot_stations_daily.parquet", index=False)
    print(f"Done. Total daily station rows: {len(df_all)}")


if __name__ == "__main__":
    main()
