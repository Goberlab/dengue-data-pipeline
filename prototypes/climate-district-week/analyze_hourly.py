# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "geopandas>=1.0",
#   "netcdf4>=1.7",
#   "numpy>=2.0",
#   "pandas>=2.2",
#   "pyarrow>=17.0",
#   "rasterio>=1.4",
#   "shapely>=2.0",
#   "xarray>=2024.10",
# ]
# ///
"""Analyze hourly ERA5-Land aggregation rules on the Peru pilot:
1. Area-weighted vs GHS-POP 2020 population-weighted (drop-NaN vs nearest-land reassignment)
   vs cell-centroid mean, highlighting Ayabaca, Huancabamba, and coastal ocean-masked districts.
2. America/Lima (UTC-5) vs UTC day boundaries for tmean, tmax, tmin, humr, ptot.
3. Hourly RH (Alduchov-Eskridge / Magnus over water) vs RH from daily-mean T/Td vs weekly-mean T/Td.
4. Weekly mean of daily max/min vs weekly absolute max/min.
5. Exact forensic comparison against CDC Peru Observatorio district-week values.
6. Verification of 2-hour (00:00 + 05:00 UTC) total_precipitation formula vs 24-hour sum.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import Point, box
import xarray as xr

MAIN_DATA = Path("/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data")
PROTO = MAIN_DATA / "prototypes/climate-district-week"
GPKG_PATH = MAIN_DATA / "raw/inei-ide-distrito/DISTRITO.gpkg"


def rh_water(t_c: np.ndarray, td_c: np.ndarray) -> np.ndarray:
    """Relative humidity (%) over liquid water (Alduchov & Eskridge 1996 / Magnus)."""
    es = np.exp((17.625 * t_c) / (243.04 + t_c))
    e = np.exp((17.625 * td_c) / (243.04 + td_c))
    return np.clip(100.0 * (e / es), 0.0, 100.0)


def rh_ecmwf_ifs(t_k: np.ndarray, td_k: np.ndarray) -> np.ndarray:
    """ECMWF IFS Tetens saturation vapour pressure over water (a1=611.21, a3=17.502, a4=32.19)."""
    t0 = 273.16
    es = 611.21 * np.exp(17.502 * (t_k - t0) / (t_k - 32.19))
    e = 611.21 * np.exp(17.502 * (td_k - t0) / (td_k - 32.19))
    return np.clip(100.0 * (e / es), 0.0, 100.0)


def build_pop_reassigned_weights(
    ds_ref: xr.Dataset,
    weights_base: pd.DataFrame,
) -> pd.DataFrame:
    """Add w_pop_reassigned: population falling inside ocean-masked ERA5-Land cells
    is reassigned to the nearest valid ERA5-Land land cell instead of being dropped.
    """
    cache = PROTO / "weights/weights_era5_land_full.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    lats = ds_ref["latitude"].values
    lons = ds_ref["longitude"].values
    valid = ~np.isnan(ds_ref["t2m"].isel(valid_time=0).values)

    # Precompute nearest valid (i, j) for every ocean cell using UTM coordinates
    cells = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            cells.append(
                {
                    "i": i,
                    "j": j,
                    "lat": float(lat),
                    "lon": float(lon),
                    "is_valid": bool(valid[i, j]),
                    "geometry": box(lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05),
                }
            )
    grid_4326 = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    centers_utm = gpd.GeoSeries(
        [Point(r["lon"], r["lat"]) for _, r in grid_4326.iterrows()], crs="EPSG:4326"
    ).to_crs(epsg=32717)
    grid_4326["cx"] = centers_utm.x.values
    grid_4326["cy"] = centers_utm.y.values

    val_df = grid_4326[grid_4326["is_valid"]].copy()
    nearest_map: dict[tuple[int, int], tuple[int, int]] = {}
    for _, r in grid_4326.iterrows():
        if r["is_valid"]:
            nearest_map[(int(r["i"]), int(r["j"]))] = (int(r["i"]), int(r["j"]))
        else:
            d2 = (val_df["cx"].values - r["cx"]) ** 2 + (val_df["cy"].values - r["cy"]) ** 2
            best = val_df.iloc[int(np.argmin(d2))]
            nearest_map[(int(r["i"]), int(r["j"]))] = (int(best["i"]), int(best["j"]))

    g = gpd.read_file(GPKG_PATH)
    g["ubigeo"] = g["ubigeo"].astype(str).str.zfill(6)
    pilot = g[g["ubigeo"].str[:2].isin({"14", "20", "24"})].sort_values("ubigeo").reset_index(drop=True)

    pop_src = rasterio.open(PROTO / "ghspop/ghspop_e2020_3ss_pilot.tif")
    nodata = pop_src.nodata

    def pop_in_geom(geom) -> float:
        if geom.is_empty:
            return 0.0
        try:
            out, _ = rio_mask(pop_src, [geom], crop=True, all_touched=False)
        except ValueError:
            return 0.0
        data = out[0].astype(np.float64)
        if nodata is not None:
            data = np.where(data == nodata, 0.0, data)
        data = np.where(np.isnan(data) | (data < 0), 0.0, data)
        return float(data.sum())

    reassigned_rows: list[dict] = []
    for _, d in pilot.iterrows():
        ub = d["ubigeo"]
        geom = d.geometry
        ov = grid_4326[grid_4326.intersects(geom)]
        acc: dict[tuple[int, int], float] = {}
        for _, cell in ov.iterrows():
            p = pop_in_geom(cell.geometry.intersection(geom))
            if p <= 0:
                continue
            ti, tj = nearest_map[(int(cell["i"]), int(cell["j"]))]
            acc[(ti, tj)] = acc.get((ti, tj), 0.0) + p
        tot = sum(acc.values())
        if tot > 0:
            for (ti, tj), val in acc.items():
                reassigned_rows.append({"ubigeo": ub, "i": ti, "j": tj, "w_pop_reassigned": val / tot})
    pop_src.close()

    df_r = pd.DataFrame(reassigned_rows)
    merged = pd.merge(
        weights_base[["ubigeo", "i", "j", "w_area", "w_pop", "w_center"]],
        df_r,
        on=["ubigeo", "i", "j"],
        how="outer",
    ).fillna(0.0)
    merged.to_parquet(cache, index=False)
    return merged


def hourly_tp_increment(ds: xr.Dataset) -> np.ndarray:
    """Convert ERA5-Land cumulative tp (m) to hourly increments (mm).
    At 01:00 UTC, tp is the 00:00-01:00 increment.
    At 02:00..23:00 and 00:00 (next day), increment = tp(t) - tp(t-1).
    First timestamp (index 0) is set to NaN if hour != 1.
    """
    tp_mm = ds["tp"].values * 1000.0
    times = pd.to_datetime(ds["valid_time"].values)
    inc = np.full_like(tp_mm, np.nan, dtype=np.float64)
    for idx, ts in enumerate(times):
        if ts.hour == 1:
            inc[idx] = tp_mm[idx]
        elif idx > 0 and (times[idx] - times[idx - 1]) == pd.Timedelta(hours=1):
            inc[idx] = np.maximum(0.0, tp_mm[idx] - tp_mm[idx - 1])
    return inc


def aggregate_month(nc_path: Path, weights: pd.DataFrame, cal: pd.DataFrame, tag: str) -> pd.DataFrame:
    ds = xr.open_dataset(nc_path)
    times_utc = pd.to_datetime(ds["valid_time"].values)
    t2m_c = ds["t2m"].values - 273.15
    d2m_c = ds["d2m"].values - 273.15
    rh_h = rh_water(t2m_c, d2m_c)
    rh_ifs = rh_ecmwf_ifs(ds["t2m"].values, ds["d2m"].values)
    tp_h = hourly_tp_increment(ds)

    # Verify 2-hour tp formula against 24-hour sum for Lima days
    tp_raw_mm = ds["tp"].values * 1000.0
    time_to_idx = {ts: idx for idx, ts in enumerate(times_utc)}

    # Check exact identity on a sample full Lima day inside the month
    sample_dates = sorted({ts.date() for ts in times_utc})[2:-2]
    max_formula_err = 0.0
    for d in sample_dates:
        # Lima day d = 05:00 UTC day d to 05:00 UTC day d+1 -> hourly increments ending 06:00 day d .. 05:00 day d+1
        ts_05_d = pd.Timestamp(d) + pd.Timedelta(hours=5)
        ts_00_d1 = pd.Timestamp(d) + pd.Timedelta(days=1)
        ts_05_d1 = pd.Timestamp(d) + pd.Timedelta(days=1, hours=5)
        if ts_05_d in time_to_idx and ts_00_d1 in time_to_idx and ts_05_d1 in time_to_idx:
            hrs = [pd.Timestamp(d) + pd.Timedelta(hours=h) for h in range(6, 30)]
            if all(h in time_to_idx for h in hrs):
                sum_24h = np.sum([tp_h[time_to_idx[h]] for h in hrs], axis=0)
                formula_2h = (
                    tp_raw_mm[time_to_idx[ts_00_d1]]
                    - tp_raw_mm[time_to_idx[ts_05_d]]
                    + tp_raw_mm[time_to_idx[ts_05_d1]]
                )
                diff = np.nanmax(np.abs(sum_24h - formula_2h))
                max_formula_err = max(max_formula_err, float(diff))
    print(f"[{tag}] Max |24h sum - 2h formula| for Lima daily rain across all cells/days: {max_formula_err:.6f} mm")

    # Pre-index weights by ubigeo
    ubigeos = sorted(weights["ubigeo"].unique())
    w_groups = {}
    for ub, grp in weights.groupby("ubigeo"):
        ii = grp["i"].values.astype(int)
        jj = grp["j"].values.astype(int)
        w_groups[ub] = (
            ii,
            jj,
            grp["w_area"].values,
            grp["w_pop"].values,
            grp["w_pop_reassigned"].values,
            grp["w_center"].values,
        )

    # Compute district hourly time series for each weighting scheme
    # Shape: (T, U)
    n_t = len(times_utc)
    n_u = len(ubigeos)

    schemes = ["area", "pop", "pop_reassigned", "center"]
    results = []

    # Map timestamps to calendar date in UTC and America/Lima (UTC-5)
    # Note: for instantaneous variables (t2m, d2m, rh), hour h UTC belongs to Lima time h-5.
    # For precipitation increment ending at hour h UTC (covering h-1..h), interval midpoint is h-0.5 UTC = h-5.5 Lima.
    # So UTC day D covers increments ending 01:00..24:00 UTC (= 00:00 next day).
    # Lima day D covers increments ending 06:00 UTC day D .. 05:00 UTC day D+1.
    cal_map = cal.set_index("date")[["epi_year", "epi_week"]].to_dict("index")

    date_utc_inst = times_utc.normalize()
    date_lima_inst = (times_utc - pd.Timedelta(hours=5)).normalize()
    date_utc_tp = (times_utc - pd.Timedelta(hours=1)).normalize()
    date_lima_tp = (times_utc - pd.Timedelta(hours=6)).normalize()

    # Precompute full epi-weeks present in this month (all 7 days have 24 hours in both UTC and Lima)
    day_counts_utc = pd.Series(date_utc_inst).value_counts()
    day_counts_lima = pd.Series(date_lima_inst).value_counts()
    day_counts_tp_lima = pd.Series(date_lima_tp[~np.isnan(tp_h[:, 20, 15])]).value_counts()

    full_days_utc = set(day_counts_utc[day_counts_utc == 24].index)
    full_days_lima = set(day_counts_lima[day_counts_lima == 24].index) & set(
        day_counts_tp_lima[day_counts_tp_lima == 24].index
    )

    ew_days: dict[tuple[int, int], list[pd.Timestamp]] = {}
    for dt, row in cal_map.items():
        key = (int(row["epi_year"]), int(row["epi_week"]))
        ew_days.setdefault(key, []).append(dt)

    full_ews = sorted(
        k
        for k, dlist in ew_days.items()
        if len(dlist) == 7 and all((d in full_days_utc and d in full_days_lima) for d in dlist)
    )
    print(f"[{tag}] Full epi-weeks available in both UTC and Lima (24h/day): {full_ews}")

    for sc_idx, sc in enumerate(schemes):
        # Compute district-hourly arrays
        dist_t = np.zeros((n_t, n_u), dtype=np.float64)
        dist_td = np.zeros((n_t, n_u), dtype=np.float64)
        dist_rh = np.zeros((n_t, n_u), dtype=np.float64)
        dist_rh_ifs = np.zeros((n_t, n_u), dtype=np.float64)
        dist_tp = np.zeros((n_t, n_u), dtype=np.float64)

        for u_idx, ub in enumerate(ubigeos):
            ii, jj, wa, wp, wpr, wc = w_groups[ub]
            w = [wa, wp, wpr, wc][sc_idx]
            mask_nz = w > 0
            ii, jj, w = ii[mask_nz], jj[mask_nz], w[mask_nz]
            dist_t[:, u_idx] = t2m_c[:, ii, jj] @ w
            dist_td[:, u_idx] = d2m_c[:, ii, jj] @ w
            dist_rh[:, u_idx] = rh_h[:, ii, jj] @ w
            dist_rh_ifs[:, u_idx] = rh_ifs[:, ii, jj] @ w
            dist_tp[:, u_idx] = tp_h[:, ii, jj] @ w

        for tz_name, d_inst, d_tp in [
            ("lima", date_lima_inst, date_lima_tp),
            ("utc", date_utc_inst, date_utc_tp),
        ]:
            for ey, ew in full_ews:
                dlist = sorted(ew_days[(ey, ew)])
                # Daily stats then weekly averages/extremes
                daily_tmean = []
                daily_tmax = []
                daily_tmin = []
                daily_tdmean = []
                daily_rh_hourly = []
                daily_rh_ifs = []
                daily_rh_from_daily = []
                daily_tp = []
                for d in dlist:
                    mi = d_inst == d
                    mt = d_tp == d
                    tm = dist_t[mi].mean(axis=0)
                    tdm = dist_td[mi].mean(axis=0)
                    daily_tmean.append(tm)
                    daily_tmax.append(dist_t[mi].max(axis=0))
                    daily_tmin.append(dist_t[mi].min(axis=0))
                    daily_tdmean.append(tdm)
                    daily_rh_hourly.append(dist_rh[mi].mean(axis=0))
                    daily_rh_ifs.append(dist_rh_ifs[mi].mean(axis=0))
                    daily_rh_from_daily.append(rh_water(tm, tdm))
                    daily_tp.append(dist_tp[mt].sum(axis=0))

                daily_tmean = np.stack(daily_tmean)  # (7, U)
                daily_tmax = np.stack(daily_tmax)
                daily_tmin = np.stack(daily_tmin)
                daily_tdmean = np.stack(daily_tdmean)
                daily_rh_hourly = np.stack(daily_rh_hourly)
                daily_rh_ifs = np.stack(daily_rh_ifs)
                daily_rh_from_daily = np.stack(daily_rh_from_daily)
                daily_tp = np.stack(daily_tp)

                wk_tmean = daily_tmean.mean(axis=0)
                wk_tdmean = daily_tdmean.mean(axis=0)
                wk_tmax_mean = daily_tmax.mean(axis=0)
                wk_tmin_mean = daily_tmin.mean(axis=0)
                wk_tmax_abs = daily_tmax.max(axis=0)
                wk_tmin_abs = daily_tmin.min(axis=0)
                wk_rh_hourly = daily_rh_hourly.mean(axis=0)
                wk_rh_ifs = daily_rh_ifs.mean(axis=0)
                wk_rh_from_daily = daily_rh_from_daily.mean(axis=0)
                wk_rh_from_weekly = rh_water(wk_tmean, wk_tdmean)
                wk_ptot = daily_tp.sum(axis=0)

                for u_idx, ub in enumerate(ubigeos):
                    results.append(
                        {
                            "tag": tag,
                            "scheme": sc,
                            "tz": tz_name,
                            "epi_year": ey,
                            "epi_week": ew,
                            "ubigeo": ub,
                            "tmean": wk_tmean[u_idx],
                            "tmax_mean": wk_tmax_mean[u_idx],
                            "tmin_mean": wk_tmin_mean[u_idx],
                            "tmax_abs": wk_tmax_abs[u_idx],
                            "tmin_abs": wk_tmin_abs[u_idx],
                            "rh_hourly": wk_rh_hourly[u_idx],
                            "rh_ifs": wk_rh_ifs[u_idx],
                            "rh_from_daily": wk_rh_from_daily[u_idx],
                            "rh_from_weekly": wk_rh_from_weekly[u_idx],
                            "ptot": wk_ptot[u_idx],
                        }
                    )

    ds.close()
    return pd.DataFrame(results)


def main() -> None:
    cal = pd.read_parquet(PROTO / "minsa_calendar.parquet")
    obs = pd.read_parquet(PROTO / "observatorio_pilot.parquet")
    w_base = pd.read_parquet(PROTO / "weights/weights_era5_land.parquet")
    diag = pd.read_parquet(PROTO / "weights/diag_era5_land.parquet")

    nc_files = sorted((PROTO / "era5land").glob("era5land_hourly_*.nc"))
    if not nc_files:
        raise FileNotFoundError("No hourly ERA5-Land files found")

    ds0 = xr.open_dataset(nc_files[0])
    weights = build_pop_reassigned_weights(ds0, w_base)
    ds0.close()

    dfs = [aggregate_month(p, weights, cal, p.stem.replace("era5land_", "")) for p in nc_files]
    df = pd.concat(dfs, ignore_index=True)
    df.to_parquet(PROTO / "hourly_experiment_results.parquet", index=False)

    # --- 1. Lima vs UTC day boundaries (using area mean) ---
    sub_a = df[df["scheme"] == "area"]
    piv_tz = sub_a.pivot(
        index=["epi_year", "epi_week", "ubigeo"],
        columns="tz",
        values=["tmean", "tmax_mean", "tmin_mean", "rh_hourly", "ptot"],
    )
    print("\n=== 1. AMERICA/LIMA vs UTC DAY BOUNDARIES (area mean, all pilot districts) ===")
    for var in ["tmean", "tmax_mean", "tmin_mean", "rh_hourly", "ptot"]:
        diff = piv_tz[(var, "lima")] - piv_tz[(var, "utc")]
        print(
            f"  {var:10s}: mean_diff={diff.mean():+.4f}, MAE={diff.abs().mean():.4f}, "
            f"p95_abs={diff.abs().quantile(0.95):.4f}, max_abs={diff.abs().max():.4f}, "
            f"corr={piv_tz[(var,'lima')].corr(piv_tz[(var,'utc')]):.6f}"
        )

    # --- 2. RH hourly vs daily-mean T/Td vs weekly-mean T/Td ---
    lima_a = df[(df["scheme"] == "area") & (df["tz"] == "lima")]
    print("\n=== 2. RELATIVE HUMIDITY: HOURLY vs DAILY-MEAN T/Td vs WEEKLY-MEAN T/Td (Lima, area) ===")
    for label, col in [
        ("RH_daily_TTd - RH_hourly", "rh_from_daily"),
        ("RH_weekly_TTd - RH_hourly", "rh_from_weekly"),
        ("RH_ECMWF_IFS - RH_Magnus", "rh_ifs"),
    ]:
        d = lima_a[col] - lima_a["rh_hourly"]
        print(
            f"  {label:28s}: bias={d.mean():+.3f} pp, MAE={d.abs().mean():.3f} pp, "
            f"p95={d.abs().quantile(0.95):.3f} pp, max={d.abs().max():.3f} pp"
        )

    # --- 3. Area vs Pop (drop-NaN) vs Pop (reassigned) vs Cell-center ---
    lima = df[df["tz"] == "lima"]
    piv_sc = lima.pivot(
        index=["epi_year", "epi_week", "ubigeo"],
        columns="scheme",
        values=["tmean", "tmax_mean", "tmin_mean", "rh_hourly", "ptot"],
    )
    print("\n=== 3. SPATIAL WEIGHTING: POP vs AREA (Lima, all 116 pilot districts) ===")
    for sc in ["pop", "pop_reassigned", "center"]:
        print(f"  -- {sc} minus area --")
        for var in ["tmean", "tmax_mean", "tmin_mean", "rh_hourly", "ptot"]:
            d = piv_sc[(var, sc)] - piv_sc[(var, "area")]
            print(
                f"    {var:10s}: mean={d.mean():+.3f}, MAE={d.abs().mean():.3f}, "
                f"p95={d.abs().quantile(0.95):.3f}, max={d.abs().max():.3f}"
            )

    # Stress-test districts: Ayabaca, Huancabamba, and top coastal ocean-masked districts
    stress_ubs = [
        "200201",  # Ayabaca
        "200202",  # Frias
        "200206",  # Pacaipampa
        "200301",  # Huancabamba
        "200302",  # Canchaque
        "200304",  # Huarmaca
        "140203",  # Incahuasi (Lambayeque Andes)
        "140114",  # Santa Rosa (0.4% land)
        "140104",  # Eten Puerto (6.7% land)
        "140108",  # Monsefu (37.6% land)
        "240101",  # Tumbes (52.1% land)
        "240103",  # La Cruz (0.3% valid pop)
        "240201",  # Zorritos (7.4% valid pop)
    ]
    diag_idx = diag.set_index("ubigeo")
    print("\n=== 4. STRESS-TEST DISTRICTS (mean over full epi-weeks in sample, Lima) ===")
    m_sc = lima.groupby(["ubigeo", "scheme"])[["tmean", "rh_hourly", "ptot"]].mean().unstack("scheme")
    for ub in stress_ubs:
        if ub not in m_sc.index:
            continue
        r = diag_idx.loc[ub]
        t_a = m_sc.loc[ub, ("tmean", "area")]
        t_p = m_sc.loc[ub, ("tmean", "pop")]
        t_pr = m_sc.loc[ub, ("tmean", "pop_reassigned")]
        p_a = m_sc.loc[ub, ("ptot", "area")]
        p_p = m_sc.loc[ub, ("ptot", "pop")]
        p_pr = m_sc.loc[ub, ("ptot", "pop_reassigned")]
        print(
            f"  {ub} {r['dist']:16s} (landA={r['valid_area_frac']:.3f}, landP={r['valid_pop_frac']:.3f}): "
            f"T area={t_a:.2f} pop={t_p:.2f} ({t_p-t_a:+.2f}) popR={t_pr:.2f} ({t_pr-t_a:+.2f}) | "
            f"P area={p_a:.1f} pop={p_p:.1f} popR={p_pr:.1f}"
        )

    # --- 5. Forensic comparison vs CDC Observatorio ---
    schemes = ["area", "pop", "pop_reassigned", "center"]
    print("\n=== 4b. TOP 15 DISTRICTS BY |pop - area| IN TMEAN (Lima) ===")
    m_diff = (m_sc[("tmean", "pop")] - m_sc[("tmean", "area")]).dropna()
    top15 = m_diff.reindex(m_diff.abs().sort_values(ascending=False).index).head(15)
    for ub, val in top15.items():
        r = diag_idx.loc[ub]
        print(
            f"  {ub} {r['dep']:10s} {r['prov']:12s} {r['dist']:22s}: "
            f"area={m_sc.loc[ub,('tmean','area')]:.2f}, pop={m_sc.loc[ub,('tmean','pop')]:.2f} (diff={val:+.2f} C)"
        )

    print("\n=== 5. COMPARISON AGAINST CDC OBSERVATORIO (all 116 pilot districts) ===")
    for sc in schemes:
        for tz in ["lima", "utc"]:
            sub = df[(df["scheme"] == sc) & (df["tz"] == tz)].merge(
                obs[["ubigeo", "epi_year", "epi_week", "tmean", "tmax", "tmin", "humr", "ptot"]],
                on=["ubigeo", "epi_year", "epi_week"],
                suffixes=("_ours", "_obs"),
            )
            mae_tm = (sub["tmean_ours"] - sub["tmean_obs"]).abs().mean()
            mae_tx = (sub["tmax_mean"] - sub["tmax"]).abs().mean()
            mae_tn = (sub["tmin_mean"] - sub["tmin"]).abs().mean()
            mae_rh = (sub["rh_hourly"] - sub["humr"]).abs().mean()
            mae_rh_d = (sub["rh_from_daily"] - sub["humr"]).abs().mean()
            mae_pt = (sub["ptot_ours"] - sub["ptot_obs"]).abs().mean()
            r_pt = sub["ptot_ours"].corr(sub["ptot_obs"])
            print(
                f"  {sc:14s} {tz:4s} (n={len(sub)}): "
                f"MAE tmean={mae_tm:.3f}, tmax={mae_tx:.3f}, tmin={mae_tn:.3f}, "
                f"rh_h={mae_rh:.3f}, rh_d={mae_rh_d:.3f}, ptot={mae_pt:.2f} (r={r_pt:.4f})"
            )


if __name__ == "__main__":
    main()
