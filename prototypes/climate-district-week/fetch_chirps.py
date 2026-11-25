# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "netcdf4>=1.7",
#   "numpy>=2.0",
#   "rasterio>=1.4",
#   "xarray>=2024.10",
# ]
# ///
"""Politely download CHIRPS v3.0 Peru subsets from data.chc.ucsb.edu using small TIFFs.

Uses small per-day GeoTIFFs (~11 MB) and LatAm-cropped pentad GeoTIFFs (~3.3 MB) with
2.5 s pauses between strictly sequential requests, clipping each file to Peru
(lon -81.6..-68.4, lat -18.6..0.2) immediately and deleting the temporary download.
"""

from __future__ import annotations

import datetime as dt
import subprocess
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds
import xarray as xr

DATA_DIR = Path(
    "/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week"
)
OUT_DIR = DATA_DIR / "chirps_v3_peru"
PERU_BOUNDS = (-81.6, -18.6, -68.4, 0.2)


def curl_download(url: str, dst: Path, timeout_s: int = 90) -> None:
    for attempt in range(5):
        proc = subprocess.run(
            [
                "curl",
                "-fsSL",
                "--max-time",
                str(timeout_s),
                "--speed-limit",
                "4096",
                "--speed-time",
                "30",
                url,
                "-o",
                str(dst),
            ],
            check=False,
        )
        if proc.returncode == 0 and dst.exists() and dst.stat().st_size > 1000:
            return
        if dst.exists():
            dst.unlink()
        wait_s = 15 * (attempt + 1)
        print(f"  retry {attempt + 1}/5 for {url.rsplit('/', 1)[-1]} after {wait_s}s (rc={proc.returncode})")
        time.sleep(wait_s)
    raise RuntimeError(f"Failed to download {url}")


def read_tif_peru(tif_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with rasterio.open(tif_path) as src:
        win = from_bounds(*PERU_BOUNDS, src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win).astype(np.float32)
        tr = src.window_transform(win)
        h, w = arr.shape
        lons = tr.c + (np.arange(w) + 0.5) * tr.a
        lats = tr.f + (np.arange(h) + 0.5) * tr.e
    return arr, lats, lons


def fetch_daily_stack(dates: list[dt.date], flavor: str, out_nc: Path) -> None:
    if out_nc.exists():
        print(f"[cached] {out_nc.name} ({out_nc.stat().st_size / 1e6:.2f} MB)")
        return
    slices = []
    lats = lons = None
    for idx, d in enumerate(dates):
        if idx > 0:
            time.sleep(2.5)
        if flavor == "prelim":
            url = (
                f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/prelim/sat/"
                f"{d.year}/chirps-v3.0.prelim.{d.year}.{d.month:02d}.{d.day:02d}.tif"
            )
        else:
            url = (
                f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/"
                f"{d.year}/chirps-v3.0.sat.{d.year}.{d.month:02d}.{d.day:02d}.tif"
            )
        tmp = OUT_DIR / f".tmp_{flavor}_{d.isoformat()}.tif"
        curl_download(url, tmp, timeout_s=120)
        arr, lats, lons = read_tif_peru(tmp)
        tmp.unlink()
        slices.append(arr)
        if (idx + 1) % 7 == 0 or idx + 1 == len(dates):
            print(f"  [{out_nc.stem}] {idx + 1}/{len(dates)} ({d.isoformat()})")

    ds = xr.Dataset(
        {"precip": (("time", "latitude", "longitude"), np.stack(slices, axis=0))},
        coords={
            "time": np.array([np.datetime64(d.isoformat()) for d in dates]),
            "latitude": lats,
            "longitude": lons,
        },
    )
    ds.to_netcdf(out_nc, encoding={"precip": {"zlib": True, "complevel": 4}})
    ds.close()
    print(f"  -> saved {out_nc.name} ({out_nc.stat().st_size / 1e6:.2f} MB)")


def fetch_pentad_pairs_2026() -> None:
    out_nc = OUT_DIR / "chirps_v3_pentads_2026_prelim_vs_final_peru.nc"
    if out_nc.exists():
        print(f"[cached] {out_nc.name} ({out_nc.stat().st_size / 1e6:.2f} MB)")
        return
    keys = [(2026, m, p) for m in range(1, 11) for p in (1, 3, 5)]
    pre_slices, fin_slices, labels = [], [], []
    lats = lons = None
    for idx, (yr, mo, p) in enumerate(keys):
        tag = f"{yr}.{mo:02d}.{p}"
        u_pre = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/prelim/pentads/latam/tifs/chirps-v3.0.{tag}.tif"
        u_fin = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/pentads/latam/tifs/chirps-v3.0.{tag}.tif"
        t_pre = OUT_DIR / f".tmp_ppre_{tag}.tif"
        t_fin = OUT_DIR / f".tmp_pfin_{tag}.tif"
        if idx > 0:
            time.sleep(2.5)
        curl_download(u_pre, t_pre, timeout_s=90)
        a_pre, lats, lons = read_tif_peru(t_pre)
        t_pre.unlink()
        time.sleep(2.5)
        curl_download(u_fin, t_fin, timeout_s=90)
        a_fin, _, _ = read_tif_peru(t_fin)
        t_fin.unlink()
        pre_slices.append(a_pre)
        fin_slices.append(a_fin)
        labels.append(tag)
        if (idx + 1) % 6 == 0 or idx + 1 == len(keys):
            print(f"  [pentads 2026] {idx + 1}/{len(keys)} ({tag})")

    ds = xr.Dataset(
        {
            "prelim": (("pentad", "latitude", "longitude"), np.stack(pre_slices, axis=0)),
            "final": (("pentad", "latitude", "longitude"), np.stack(fin_slices, axis=0)),
        },
        coords={"pentad": labels, "latitude": lats, "longitude": lons},
    )
    ds.to_netcdf(
        out_nc,
        encoding={"prelim": {"zlib": True, "complevel": 4}, "final": {"zlib": True, "complevel": 4}},
    )
    ds.close()
    print(f"  -> saved {out_nc.name} ({out_nc.stat().st_size / 1e6:.2f} MB)")


def fetch_pentads_2023_2025() -> None:
    """Fetch 36 LatAm final pentads (1 per month across 2023-2025, pentad 3 = days 11-15)
    for full 3-year seasonal comparison vs PISCOp/ERA5-Land and national -9999 gap audit."""
    out_nc = OUT_DIR / "chirps_v3_pentads_2023_2025_final_peru.nc"
    if out_nc.exists():
        print(f"[cached] {out_nc.name} ({out_nc.stat().st_size / 1e6:.2f} MB)")
        return
    keys = [(yr, m, 3) for yr in (2023, 2024, 2025) for m in range(1, 13)]
    slices, labels = [], []
    lats = lons = None
    for idx, (yr, mo, p) in enumerate(keys):
        tag = f"{yr}.{mo:02d}.{p}"
        url = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/pentads/latam/tifs/chirps-v3.0.{tag}.tif"
        tmp = OUT_DIR / f".tmp_p2325_{tag}.tif"
        if idx > 0:
            time.sleep(2.5)
        curl_download(url, tmp, timeout_s=90)
        arr, lats, lons = read_tif_peru(tmp)
        tmp.unlink()
        slices.append(arr)
        labels.append(tag)
        if (idx + 1) % 12 == 0 or idx + 1 == len(keys):
            print(f"  [pentads 2023-2025] {idx + 1}/{len(keys)} ({tag})")

    ds = xr.Dataset(
        {"final": (("pentad", "latitude", "longitude"), np.stack(slices, axis=0))},
        coords={"pentad": labels, "latitude": lats, "longitude": lons},
    )
    ds.to_netcdf(out_nc, encoding={"final": {"zlib": True, "complevel": 4}})
    ds.close()
    print(f"  -> saved {out_nc.name} ({out_nc.stat().st_size / 1e6:.2f} MB)")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in OUT_DIR.glob(".tmp_*"):
        p.unlink()

    # 1. Daily final/sat epi-weeks across 2024 & 2025 (2023-03 already cached!)
    fetch_daily_stack(
        [dt.date(2024, 2, 11) + dt.timedelta(days=k) for k in range(14)],
        "final",
        OUT_DIR / "chirps_v3_final_sat_2024_se07_se08_peru.nc",
    )
    fetch_daily_stack(
        [dt.date(2024, 7, 7) + dt.timedelta(days=k) for k in range(14)],
        "final",
        OUT_DIR / "chirps_v3_final_sat_2024_se28_se29_peru.nc",
    )
    fetch_daily_stack(
        [dt.date(2025, 2, 9) + dt.timedelta(days=k) for k in range(14)],
        "final",
        OUT_DIR / "chirps_v3_final_sat_2025_se07_se08_peru.nc",
    )

    # 2. Daily prelim/sat vs final/sat in 2026 (3 wet epi-weeks SE07-09 + 1 dry epi-week SE28)
    dates_26_wet = [dt.date(2026, 2, 15) + dt.timedelta(days=k) for k in range(21)]
    fetch_daily_stack(dates_26_wet, "prelim", OUT_DIR / "chirps_v3_prelim_sat_2026_se07_se09_peru.nc")
    fetch_daily_stack(dates_26_wet, "final", OUT_DIR / "chirps_v3_final_sat_2026_se07_se09_peru.nc")

    dates_26_dry = [dt.date(2026, 7, 12) + dt.timedelta(days=k) for k in range(7)]
    fetch_daily_stack(dates_26_dry, "prelim", OUT_DIR / "chirps_v3_prelim_sat_2026_se28_peru.nc")
    fetch_daily_stack(dates_26_dry, "final", OUT_DIR / "chirps_v3_final_sat_2026_se28_peru.nc")

    # 3. LatAm pentads: 30 pairs across Jan-Oct 2026 + 36 monthly pentads across 2023-2025
    fetch_pentad_pairs_2026()
    fetch_pentads_2023_2025()
    print("All CHIRPS v3 Peru subsets complete.")


if __name__ == "__main__":
    main()
