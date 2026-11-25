# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "cdsapi>=0.7.7",
# ]
# ///
"""Fetch ERA5-Land subsets for the Peru pilot strictly one request at a time.

Respects ECMWF October 2026 CDS protection measures:
- Strictly sequential (one request at a time, never concurrent).
- Uses "download_format": "unarchived" and NetCDF format.
- Stops immediately on any HTTP 403/429 or unexpected API error.
- Never prints or logs ~/.cdsapirc contents.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cdsapi

OUT_DIR = Path(
    "/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week/era5land"
)
PILOT_AREA = [-3.2, -81.5, -7.4, -78.8]  # [N, W, S, E] covering Tumbes, Piura, Lambayeque + margin

ALL_HOURS = [f"{h:02d}:00" for h in range(24)]
ALL_DAYS = [f"{d:02d}" for d in range(1, 32)]
ALL_MONTHS = [f"{m:02d}" for m in range(1, 13)]

TARGETS: dict[str, tuple[str, dict]] = {
    "hourly_2023_03": (
        "reanalysis-era5-land",
        {
            "variable": ["2m_temperature", "2m_dewpoint_temperature", "total_precipitation"],
            "year": "2023",
            "month": "03",
            "day": ALL_DAYS,
            "time": ALL_HOURS,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "hourly_2024_07": (
        "reanalysis-era5-land",
        {
            "variable": ["2m_temperature", "2m_dewpoint_temperature", "total_precipitation"],
            "year": "2024",
            "month": "07",
            "day": ALL_DAYS,
            "time": ALL_HOURS,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "tp_2023": (
        "reanalysis-era5-land",
        {
            "variable": ["total_precipitation"],
            "year": "2023",
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ["00:00", "05:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "tp_2024": (
        "reanalysis-era5-land",
        {
            "variable": ["total_precipitation"],
            "year": "2024",
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ["00:00", "05:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "tp_2025": (
        "reanalysis-era5-land",
        {
            "variable": ["total_precipitation"],
            "year": "2025",
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ["00:00", "05:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "tp_2026_jan_nov": (
        "reanalysis-era5-land",
        {
            "variable": ["total_precipitation"],
            "year": "2026",
            "month": [f"{m:02d}" for m in range(1, 12)],
            "day": ALL_DAYS,
            "time": ["00:00", "05:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "t2m_d2m_3h_2023": (
        "reanalysis-era5-land",
        {
            "variable": ["2m_temperature", "2m_dewpoint_temperature"],
            "year": "2023",
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "t2m_d2m_3h_2024": (
        "reanalysis-era5-land",
        {
            "variable": ["2m_temperature", "2m_dewpoint_temperature"],
            "year": "2024",
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
    "t2m_d2m_3h_2025": (
        "reanalysis-era5-land",
        {
            "variable": ["2m_temperature", "2m_dewpoint_temperature"],
            "year": "2025",
            "month": ALL_MONTHS,
            "day": ALL_DAYS,
            "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": PILOT_AREA,
        },
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="+", choices=list(TARGETS.keys()))
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client()

    for idx, name in enumerate(args.targets):
        out_path = OUT_DIR / f"era5land_{name}.nc"
        if out_path.exists():
            print(f"[cached] {out_path.name} ({out_path.stat().st_size / 1e6:.2f} MB)")
            continue
        if idx > 0:
            time.sleep(5)
        dataset, req = TARGETS[name]
        print(f"Requesting {name} from {dataset}...")
        t0 = time.time()
        try:
            client.retrieve(dataset, req, str(out_path))
        except Exception as exc:
            print(f"STOPPING on error for {name}: {exc}", file=sys.stderr)
            sys.exit(2)
        print(
            f"  -> {out_path.name} ({out_path.stat().st_size / 1e6:.2f} MB) in {time.time() - t0:.1f}s"
        )


if __name__ == "__main__":
    main()
