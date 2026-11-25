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
"""Comprehensive precipitation prototype analysis:
1. Full 3-year (2023-2025) ERA5-Land tp vs PISCOp v3.0 vs CDC Observatorio ptot (116 pilot districts).
2. CHIRPS v3.0 final/sat vs ERA5-Land tp vs PISCOp v3.0 vs Observatorio over overlapping wet & dry
   epi-weeks (2023-03, 2024-02, 2024-07, 2025-02), both area-weighted and population-weighted.
3. CHIRPS v3.0 prelim/sat vs final/sat revision magnitude:
   (a) exact daily epi-weeks (2026-SE05..SE10 wet + 2026-SE28 dry),
   (b) 30 pentads spanning Jan-Oct 2026 (full seasonal cycle).
4. Post-2022 -9999 IR gap audit across Peru (all 1,890 districts) and pilot (116 districts).
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.mask import mask as rio_mask
from rasterio.transform import from_origin
from shapely.geometry import Point, box
import xarray as xr

MAIN_DATA = Path("/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data")
PROTO = MAIN_DATA / "prototypes/climate-district-week"
CHIRPS_DIR = PROTO / "chirps_v3_peru"
GPKG_PATH = MAIN_DATA / "raw/inei-ide-distrito/DISTRITO.gpkg"


def build_chirps_pilot_weights(ref_nc: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute exact area & GHS-POP 2020 weights for the 116 pilot districts on CHIRPS 0.05 deg grid."""
    w_cache = PROTO / "weights/weights_chirps_v3.parquet"
    d_cache = PROTO / "weights/diag_chirps_v3.parquet"
    if w_cache.exists() and d_cache.exists():
        return pd.read_parquet(w_cache), pd.read_parquet(d_cache)

    ds = xr.open_dataset(ref_nc, mask_and_scale=False)
    lat_name = "latitude" if "latitude" in ds.coords else "lat"
    lon_name = "longitude" if "longitude" in ds.coords else "lon"
    var_name = [v for v in ds.data_vars if ds[v].ndim == 3][0]

    lats_all = ds[lat_name].values
    lons_all = ds[lon_name].values
    # Restrict grid to pilot bbox with margin
    lat_mask = (lats_all >= -7.5) & (lats_all <= -3.1)
    lon_mask = (lons_all >= -81.6) & (lons_all <= -78.7)
    lats = lats_all[lat_mask]
    lons = lons_all[lon_mask]
    arr = ds[var_name].values[:, lat_mask, :][:, :, lon_mask]
    # A cell is valid land if >= 0 on at least one day
    valid_mask = np.any((arr >= 0) & (~np.isnan(arr)), axis=0)
    ds.close()

    g = gpd.read_file(GPKG_PATH)
    g["ubigeo"] = g["ubigeo"].astype(str).str.zfill(6)
    pilot_4326 = g[g["ubigeo"].str[:2].isin({"14", "20", "24"})].sort_values("ubigeo").reset_index(drop=True)
    pilot_utm = pilot_4326.to_crs(epsg=32717)

    cells = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            cells.append(
                {
                    "i": int(i),
                    "j": int(j),
                    "lat": float(lat),
                    "lon": float(lon),
                    "is_valid": bool(valid_mask[i, j]),
                    "geometry": box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025),
                }
            )
    grid_4326 = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    grid_utm = grid_4326.to_crs(epsg=32717)
    valid_utm = grid_utm[grid_utm["is_valid"]].copy()
    valid_utm["center_utm"] = gpd.GeoSeries(
        [Point(r["lon"], r["lat"]) for _, r in valid_utm.iterrows()], crs="EPSG:4326"
    ).to_crs(epsg=32717).values

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

    w_rows = []
    d_rows = []
    for idx_r, d_utm in pilot_utm.iterrows():
        d_4326 = pilot_4326.loc[idx_r]
        ub = d_utm["ubigeo"]
        geom_utm = d_utm.geometry
        geom_4326 = d_4326.geometry
        dist_area = float(geom_utm.area)
        dist_pop = pop_in_geom(geom_4326)

        ov_idx = grid_utm.index[grid_utm.intersects(geom_utm)].tolist()
        ov_utm = grid_utm.loc[ov_idx].copy()
        ov_4326 = grid_4326.loc[ov_idx]

        ia, ip = [], []
        for k in ov_idx:
            ia.append(float(grid_utm.at[k, "geometry"].intersection(geom_utm).area))
            ip.append(pop_in_geom(ov_4326.at[k, "geometry"].intersection(geom_4326)))
        ov_utm["inter_area"] = ia
        ov_utm["inter_pop"] = ip

        val_ov = ov_utm[ov_utm["is_valid"]].copy()
        va_sum = float(val_ov["inter_area"].sum())
        vp_sum = float(val_ov["inter_pop"].sum())
        if va_sum <= 0:
            dists = valid_utm["center_utm"].distance(geom_utm.centroid)
            nk = int(dists.idxmin())
            val_ov = grid_utm.loc[[nk]].copy()
            val_ov["inter_area"] = 1.0
            val_ov["inter_pop"] = 1.0
            va_sum = vp_sum = 1.0

        for _, r in val_ov.iterrows():
            wa = float(r["inter_area"]) / va_sum
            wp = float(r["inter_pop"]) / vp_sum if vp_sum > 0 else wa
            w_rows.append(
                {
                    "ubigeo": ub,
                    "lat": float(r["lat"]),
                    "lon": float(r["lon"]),
                    "w_area": wa,
                    "w_pop": wp,
                }
            )
        d_rows.append(
            {
                "ubigeo": ub,
                "dep": d_utm["nombdep"],
                "dist": d_utm["nombdist"],
                "n_valid_touch": len(val_ov),
                "valid_area_frac": va_sum / dist_area if dist_area > 0 else 0.0,
                "valid_pop_frac": vp_sum / dist_pop if dist_pop > 0 else np.nan,
            }
        )
    pop_src.close()
    w_df = pd.DataFrame(w_rows)
    d_df = pd.DataFrame(d_rows)
    w_df.to_parquet(w_cache, index=False)
    d_df.to_parquet(d_cache, index=False)
    return w_df, d_df


def aggregate_chirps_nc(nc_path: Path, w_chirps: pd.DataFrame, var_override: str | None = None) -> pd.DataFrame:
    """Aggregate a Peru CHIRPS NetCDF to daily pilot district area & pop means."""
    ds = xr.open_dataset(nc_path, mask_and_scale=False)
    lat_name = "latitude" if "latitude" in ds.coords else "lat"
    lon_name = "longitude" if "longitude" in ds.coords else "lon"
    var_name = var_override or [v for v in ds.data_vars if ds[v].ndim == 3][0]
    time_name = ds[var_name].dims[0]

    lats = np.round(ds[lat_name].values.astype(np.float64), 4)
    lons = np.round(ds[lon_name].values.astype(np.float64), 4)
    lat_idx = {float(v): i for i, v in enumerate(lats)}
    lon_idx = {float(v): j for j, v in enumerate(lons)}

    arr = ds[var_name].values.astype(np.float64)
    arr = np.where((arr < -9000) | np.isnan(arr), np.nan, arr)
    times = ds[time_name].values
    ds.close()

    rows = []
    for ub, g in w_chirps.groupby("ubigeo"):
        ii = np.array([lat_idx[round(float(x), 4)] for x in g["lat"].values])
        jj = np.array([lon_idx[round(float(x), 4)] for x in g["lon"].values])
        wa = g["w_area"].values
        wp = g["w_pop"].values
        vals = arr[:, ii, jj]  # (T, K)
        # Renormalize weights over non-NaN cells per timestep
        valid = ~np.isnan(vals)
        vals0 = np.where(valid, vals, 0.0)
        wa_den = (valid * wa).sum(axis=1)
        wp_den = (valid * wp).sum(axis=1)
        va = np.where(wa_den > 0, (vals0 * wa).sum(axis=1) / wa_den, np.nan)
        vp = np.where(wp_den > 0, (vals0 * wp).sum(axis=1) / wp_den, np.nan)
        for t_i, tv in enumerate(times):
            rows.append((tv, ub, float(va[t_i]), float(vp[t_i])))

    return pd.DataFrame(rows, columns=[time_name, "ubigeo", "val_area", "val_pop"])


def aggregate_era5_tp_years(cal: pd.DataFrame) -> pd.DataFrame:
    w_e5 = pd.read_parquet(PROTO / "weights/weights_era5_land_full.parquet")
    ubigeos = sorted(w_e5["ubigeo"].unique())
    nc_files = sorted((PROTO / "era5land").glob("era5land_tp_202*.nc"))
    datasets = [xr.open_dataset(p) for p in nc_files]
    ds = xr.concat(datasets, dim="valid_time").sortby("valid_time")
    times = pd.to_datetime(ds["valid_time"].values)
    tp_mm = ds["tp"].values * 1000.0
    tmap = {ts: idx for idx, ts in enumerate(times)}

    n_t, n_u = len(times), len(ubigeos)
    raw_a = np.zeros((n_t, n_u), dtype=np.float64)
    raw_p = np.zeros((n_t, n_u), dtype=np.float64)
    for u_idx, ub in enumerate(ubigeos):
        g = w_e5[w_e5["ubigeo"] == ub]
        ii, jj = g["i"].values.astype(int), g["j"].values.astype(int)
        vals = tp_mm[:, ii, jj]
        raw_a[:, u_idx] = vals @ g["w_area"].values
        raw_p[:, u_idx] = vals @ g["w_pop"].values
    for d in datasets:
        d.close()

    all_dates = pd.date_range("2023-01-01", "2025-12-30", freq="D")
    rows = []
    for d in all_dates:
        ts05 = d + pd.Timedelta(hours=5)
        ts00_1 = d + pd.Timedelta(days=1)
        ts05_1 = d + pd.Timedelta(days=1, hours=5)
        if ts00_1 in tmap and ts05 in tmap and ts05_1 in tmap:
            i05, i00_1, i05_1 = tmap[ts05], tmap[ts00_1], tmap[ts05_1]
            ua = raw_a[i00_1]
            la = np.maximum(0.0, raw_a[i00_1] - raw_a[i05] + raw_a[i05_1])
            lp = np.maximum(0.0, raw_p[i00_1] - raw_p[i05] + raw_p[i05_1])
            for u_idx, ub in enumerate(ubigeos):
                rows.append((d, ub, ua[u_idx], la[u_idx], lp[u_idx]))

    df_d = pd.DataFrame(rows, columns=["date", "ubigeo", "e5_utc_area", "e5_lima_area", "e5_lima_pop"])
    df_d = df_d.merge(cal, on="date", how="inner")
    wk = (
        df_d.groupby(["ubigeo", "epi_year", "epi_week"])
        .agg(
            n_days=("date", "count"),
            e5_utc_area=("e5_utc_area", "sum"),
            e5_lima_area=("e5_lima_area", "sum"),
            e5_lima_pop=("e5_lima_pop", "sum"),
        )
        .reset_index()
    )
    wk = wk[wk["n_days"] == 7]
    wk.to_parquet(PROTO / "era5land_tp_pilot_weekly_2023_2025.parquet", index=False)
    return wk


def audit_neg9999_gaps(nc_files: list[Path]) -> None:
    """Count genuine post-2022 -9999 IR gaps inside Peru's 1,890 districts and 116 pilot districts."""
    g = gpd.read_file(GPKG_PATH)
    g["ubigeo"] = g["ubigeo"].astype(str).str.zfill(6)
    peru_union = g.geometry.union_all()
    pilot_union = g[g["ubigeo"].str[:2].isin({"14", "20", "24"})].geometry.union_all()

    total_days = 0
    days_with_peru_gap = 0
    days_with_pilot_gap = 0
    peru_gap_cell_days = 0
    pilot_gap_cell_days = 0
    total_peru_cell_days = 0
    total_pilot_cell_days = 0
    gap_examples = []

    for p in nc_files:
        ds = xr.open_dataset(p, mask_and_scale=False)
        lat_name = "latitude" if "latitude" in ds.coords else "lat"
        lon_name = "longitude" if "longitude" in ds.coords else "lon"
        v = [k for k in ds.data_vars if ds[k].ndim == 3][0]
        lats = ds[lat_name].values
        lons = ds[lon_name].values
        arr = ds[v].values
        t_vals = pd.to_datetime(ds[ds[v].dims[0]].values)
        ds.close()

        if lats[0] < lats[-1]:
            lats = lats[::-1]
            arr = arr[:, ::-1, :]
        tr = from_origin(float(lons[0]) - 0.025, float(lats[0]) + 0.025, 0.05, 0.05)
        shape = (len(lats), len(lons))
        in_peru = ~geometry_mask([peru_union], out_shape=shape, transform=tr, invert=False)
        in_pilot = ~geometry_mask([pilot_union], out_shape=shape, transform=tr, invert=False)
        ever_valid = np.any((arr >= 0) & (~np.isnan(arr)), axis=0)
        peru_land = in_peru & ever_valid
        pilot_land = in_pilot & ever_valid
        n_pc = int(peru_land.sum())
        n_plc = int(pilot_land.sum())

        for t_i, tv in enumerate(t_vals):
            total_days += 1
            total_peru_cell_days += n_pc
            total_pilot_cell_days += n_plc
            sl = arr[t_i]
            is_gap = (sl < -9000) | np.isnan(sl)
            n_pg = int((is_gap & peru_land).sum())
            n_plg = int((is_gap & pilot_land).sum())
            if n_pg > 0:
                days_with_peru_gap += 1
                peru_gap_cell_days += n_pg
                gap_examples.append((str(tv.date()), p.name, n_pg, n_plg))
            if n_plg > 0:
                days_with_pilot_gap += 1
                pilot_gap_cell_days += n_plg

    print("\n=== 4. POST-2022 CHIRPS v3 -9999 IR GAP AUDIT (PERU & PILOT) ===")
    print(f"  Daily grids audited: {total_days} across {len(nc_files)} files")
    print(
        f"  Peru land: {days_with_peru_gap}/{total_days} days had >=1 -9999 land cell "
        f"({peru_gap_cell_days:,}/{total_peru_cell_days:,} = {100 * peru_gap_cell_days / max(1, total_peru_cell_days):.5f}% of Peru land cell-days)"
    )
    print(
        f"  Pilot land: {days_with_pilot_gap}/{total_days} days had >=1 -9999 land cell "
        f"({pilot_gap_cell_days:,}/{total_pilot_cell_days:,} = {100 * pilot_gap_cell_days / max(1, total_pilot_cell_days):.5f}% of pilot land cell-days)"
    )
    if gap_examples:
        print("  Top gap days (date, file, peru_cells, pilot_cells):")
        for ex in sorted(gap_examples, key=lambda x: -x[2])[:10]:
            print("   ", ex)


def main() -> None:
    cal = pd.read_parquet(PROTO / "minsa_calendar.parquet")
    obs = pd.read_parquet(PROTO / "observatorio_pilot.parquet")
    piscop_w = pd.read_parquet(PROTO / "piscop_pilot_weekly_2018_2025.parquet")
    diag_e5 = pd.read_parquet(PROTO / "weights/diag_era5_land.parquet")[["ubigeo", "dep", "prov", "dist"]]

    # 1. Full 3-year ERA5-Land tp (2023-2025) vs PISCOp v3 vs Observatorio
    e5_w = aggregate_era5_tp_years(cal)
    m3y = e5_w.merge(piscop_w, on=["ubigeo", "epi_year", "epi_week"]).merge(
        obs[["ubigeo", "epi_year", "epi_week", "ptot"]].rename(columns={"ptot": "obs_ptot"}),
        on=["ubigeo", "epi_year", "epi_week"],
    )
    print(f"=== 1. 3-YEAR RAINFALL (2023-2025, n={len(m3y):,} district-weeks, {m3y[['epi_year','epi_week']].drop_duplicates().shape[0]} full epi-weeks) ===")
    print(
        f"  Mean mm/wk: ERA5-Land Lima area={m3y['e5_lima_area'].mean():.2f}, UTC area={m3y['e5_utc_area'].mean():.2f}, "
        f"Lima pop={m3y['e5_lima_pop'].mean():.2f}, PISCOp area={m3y['piscop_area'].mean():.2f}, Observatorio={m3y['obs_ptot'].mean():.2f}"
    )
    for a, b in [
        ("e5_lima_area", "e5_utc_area"),
        ("e5_lima_area", "piscop_area"),
        ("e5_lima_pop", "piscop_pop"),
        ("e5_utc_area", "obs_ptot"),
        ("obs_ptot", "piscop_area"),
    ]:
        d = m3y[a] - m3y[b]
        print(
            f"  {a:14s} vs {b:12s}: bias={d.mean():+6.2f}, MAE={d.abs().mean():5.2f}, "
            f"RMSE={np.sqrt((d**2).mean()):5.2f}, r={m3y[a].corr(m3y[b]):.4f}"
        )

    m3y_z = m3y.merge(diag_e5, on="ubigeo")
    m3y_z["zone"] = np.where(
        m3y_z["prov"].isin(["AYABACA", "HUANCABAMBA"]), "Andean (Ayabaca/Huancabamba)", m3y_z["dep"]
    )
    print("  By zone (2023-2025):")
    for z, grp in m3y_z.groupby("zone"):
        print(
            f"    {z:30s}: E5={grp['e5_lima_area'].mean():5.1f}, PISCOp={grp['piscop_area'].mean():5.1f}, "
            f"Obs={grp['obs_ptot'].mean():5.1f}, r(E5,PISCOp)={grp['e5_lima_area'].corr(grp['piscop_area']):.3f}, "
            f"r(Obs,PISCOp)={grp['obs_ptot'].corr(grp['piscop_area']):.3f}"
        )

    # 2. CHIRPS v3 final/sat vs ERA5-Land vs PISCOp v3 vs Observatorio (2023-2025 sample months)
    bm_files = sorted(CHIRPS_DIR.glob("chirps_v3_final_sat_202[345]_*.nc"))
    if bm_files:
        w_chirps, d_chirps = build_chirps_pilot_weights(bm_files[0])
        print(
            f"\nCHIRPS v3 0.05 deg spatial mask: districts with valid_area_frac < 0.99: "
            f"{int((d_chirps['valid_area_frac'] < 0.99).sum())}, min={d_chirps['valid_area_frac'].min():.3f}"
        )
        ch_parts = [aggregate_chirps_nc(p, w_chirps) for p in bm_files]
        ch_d = pd.concat(ch_parts, ignore_index=True).rename(
            columns={"time": "date", "val_area": "chirps_area", "val_pop": "chirps_pop"}
        )
        ch_d["date"] = pd.to_datetime(ch_d["date"])
        ch_d = ch_d.merge(cal, on="date", how="inner")
        ch_w = (
            ch_d.groupby(["ubigeo", "epi_year", "epi_week"])
            .agg(
                n_days=("date", "count"),
                chirps_area=("chirps_area", "sum"),
                chirps_pop=("chirps_pop", "sum"),
            )
            .reset_index()
        )
        ch_w = ch_w[ch_w["n_days"] == 7]
        mc = ch_w.merge(m3y, on=["ubigeo", "epi_year", "epi_week"])
        ews = sorted(mc[["epi_year", "epi_week"]].drop_duplicates().itertuples(index=False, name=None))
        print(f"\n=== 2. CHIRPS v3 final/sat vs ERA5-LAND vs PISCOp v3 vs OBSERVATORIO ({len(ews)} full epi-weeks: {ews}, n={len(mc):,}) ===")
        print(
            f"  Mean mm/wk: CHIRPS area={mc['chirps_area'].mean():.2f}, CHIRPS pop={mc['chirps_pop'].mean():.2f}, "
            f"ERA5-Land={mc['e5_lima_area'].mean():.2f}, PISCOp={mc['piscop_area'].mean():.2f}, Obs={mc['obs_ptot'].mean():.2f}"
        )
        for a, b in [
            ("chirps_area", "piscop_area"),
            ("chirps_pop", "piscop_pop"),
            ("e5_lima_area", "piscop_area"),
            ("obs_ptot", "piscop_area"),
            ("chirps_area", "e5_lima_area"),
            ("chirps_area", "obs_ptot"),
            ("chirps_pop", "chirps_area"),
        ]:
            d = mc[a] - mc[b]
            print(
                f"  {a:14s} vs {b:12s}: bias={d.mean():+6.2f}, MAE={d.abs().mean():5.2f}, "
                f"RMSE={np.sqrt((d**2).mean()):5.2f}, r={mc[a].corr(mc[b]):.4f}"
            )
        mcz = mc.merge(diag_e5, on="ubigeo")
        mcz["zone"] = np.where(
            mcz["prov"].isin(["AYABACA", "HUANCABAMBA"]), "Andean (Ayabaca/Huancabamba)", mcz["dep"]
        )
        print("  By zone (overlapping 2023-2025 epi-weeks):")
        for z, grp in mcz.groupby("zone"):
            print(
                f"    {z:30s}: CHIRPS={grp['chirps_area'].mean():5.1f}, E5={grp['e5_lima_area'].mean():5.1f}, "
                f"PISCOp={grp['piscop_area'].mean():5.1f}, r(CH,PI)={grp['chirps_area'].corr(grp['piscop_area']):.3f}, "
                f"r(E5,PI)={grp['e5_lima_area'].corr(grp['piscop_area']):.3f}"
            )

    # 3. CHIRPS v3 prelim/sat vs final/sat revisions (2026 daily epi-weeks + 30 pentads)
    pre_26_files = sorted(CHIRPS_DIR.glob("chirps_v3_prelim_sat_2026_*.nc"))
    fin_26_files = sorted(CHIRPS_DIR.glob("chirps_v3_final_sat_2026_*.nc"))
    if pre_26_files and fin_26_files:
        w_chirps, _ = build_chirps_pilot_weights(fin_26_files[0])
        pre_d = pd.concat([aggregate_chirps_nc(p, w_chirps) for p in pre_26_files], ignore_index=True)
        pre_d = pre_d.rename(columns={"time": "date", "val_area": "pre_area", "val_pop": "pre_pop"})
        pre_d["date"] = pd.to_datetime(pre_d["date"])

        fin_d = pd.concat([aggregate_chirps_nc(p, w_chirps) for p in fin_26_files], ignore_index=True)
        fin_d = fin_d.rename(columns={"time": "date", "val_area": "fin_area", "val_pop": "fin_pop"})
        fin_d["date"] = pd.to_datetime(fin_d["date"])

        m26 = pre_d.merge(fin_d, on=["date", "ubigeo"]).merge(cal, on="date", how="inner")
        w26 = (
            m26.groupby(["ubigeo", "epi_year", "epi_week"])
            .agg(
                n_days=("date", "count"),
                pre_area=("pre_area", "sum"),
                fin_area=("fin_area", "sum"),
            )
            .reset_index()
        )
        w26 = w26[w26["n_days"] == 7]
        diff26 = w26["fin_area"] - w26["pre_area"]
        ews26 = sorted(w26[["epi_year", "epi_week"]].drop_duplicates().itertuples(index=False, name=None))
        print(f"\n=== 3a. CHIRPS v3 PRELIM vs FINAL DAILY EPI-WEEK REVISIONS (2026: {ews26}, n={len(w26)}) ===")
        print(
            f"  Mean mm/wk: prelim={w26['pre_area'].mean():.2f}, final={w26['fin_area'].mean():.2f}, "
            f"bias(fin-pre)={diff26.mean():+.2f}, MAE={diff26.abs().mean():.2f}, "
            f"median_abs={diff26.abs().median():.2f}, p95_abs={diff26.abs().quantile(0.95):.2f}, "
            f"max_abs={diff26.abs().max():.2f}, r={w26['pre_area'].corr(w26['fin_area']):.4f}"
        )
        wet26 = w26[w26["fin_area"] >= 10.0]
        dw26 = wet26["fin_area"] - wet26["pre_area"]
        print(
            f"  Wet weeks (>=10 mm final, n={len(wet26)}): mean fin={wet26['fin_area'].mean():.2f}, "
            f"bias={dw26.mean():+.2f}, MAE={dw26.abs().mean():.2f}, median_rel={((dw26.abs()/wet26['fin_area']).median()*100):.1f}%, "
            f"p95_abs={dw26.abs().quantile(0.95):.2f}"
        )
        for (_, ew), grp in w26.groupby(["epi_year", "epi_week"]):
            d = grp["fin_area"] - grp["pre_area"]
            print(
                f"    2026-SE{ew:02d}: pre={grp['pre_area'].mean():5.1f}, fin={grp['fin_area'].mean():5.1f}, "
                f"bias={d.mean():+5.2f}, MAE={d.abs().mean():5.2f}, p95={d.abs().quantile(0.95):5.1f}, r={grp['pre_area'].corr(grp['fin_area']):.4f}"
            )

    pent_path = CHIRPS_DIR / "chirps_v3_pentads_2026_prelim_vs_final_peru.nc"
    if pent_path.exists():
        w_chirps, _ = build_chirps_pilot_weights(fin_26_files[0])
        p_pre = aggregate_chirps_nc(pent_path, w_chirps, var_override="prelim").rename(
            columns={"val_area": "pre_area"}
        )
        p_fin = aggregate_chirps_nc(pent_path, w_chirps, var_override="final").rename(
            columns={"val_area": "fin_area"}
        )
        mp = p_pre[["pentad", "ubigeo", "pre_area"]].merge(
            p_fin[["pentad", "ubigeo", "fin_area"]], on=["pentad", "ubigeo"]
        )
        dp = mp["fin_area"] - mp["pre_area"]
        print(f"\n=== 3b. CHIRPS v3 PRELIM vs FINAL PENTADS (Jan-Oct 2026, 30 pentads, n={len(mp):,}) ===")
        print(
            f"  Mean mm/pentad: prelim={mp['pre_area'].mean():.2f}, final={mp['fin_area'].mean():.2f}, "
            f"bias={dp.mean():+.2f}, MAE={dp.abs().mean():.2f}, p95_abs={dp.abs().quantile(0.95):.2f}, "
            f"max_abs={dp.abs().max():.2f}, r={mp['pre_area'].corr(mp['fin_area']):.4f}"
        )
        wetp = mp[mp["fin_area"] >= 10.0]
        dwp = wetp["fin_area"] - wetp["pre_area"]
        print(
            f"  Wet pentads (>=10 mm, n={len(wetp)}): bias={dwp.mean():+.2f}, MAE={dwp.abs().mean():.2f}, "
            f"median_rel={(dwp.abs()/wetp['fin_area']).median()*100:.1f}%"
        )

    # 3c. 36 monthly pentads across 2023-2025: CHIRPS v3 final vs ERA5-Land vs PISCOp v3 (full seasonal cycle)
    p2325_path = CHIRPS_DIR / "chirps_v3_pentads_2023_2025_final_peru.nc"
    if p2325_path.exists():
        w_chirps, _ = build_chirps_pilot_weights(fin_26_files[0] if fin_26_files else bm_files[0])
        ch_p = aggregate_chirps_nc(p2325_path, w_chirps, var_override="final").rename(
            columns={"val_area": "chirps_area", "val_pop": "chirps_pop"}
        )
        # Aggregate PISCOp daily and ERA5-Land daily over exact days 11-15 of each month (pentad 3)
        p_daily = pd.read_parquet(PROTO / "piscop_pilot_daily_2018_2025.parquet")
        p_daily = p_daily[p_daily["date"].dt.year.isin([2023, 2024, 2025]) & p_daily["date"].dt.day.between(11, 15)].copy()
        p_daily["pentad"] = p_daily["date"].dt.strftime("%Y.%m.3")
        pi_p = p_daily.groupby(["pentad", "ubigeo"])[["piscop_area", "piscop_pop"]].sum().reset_index()

        # Reconstruct ERA5-Land daily Lima rain for 2023-2025 pentad 3
        w_e5 = pd.read_parquet(PROTO / "weights/weights_era5_land_full.parquet")
        ubigeos = sorted(w_e5["ubigeo"].unique())
        ds_e5 = xr.concat([xr.open_dataset(p) for p in sorted((PROTO / "era5land").glob("era5land_tp_202*.nc"))], dim="valid_time").sortby("valid_time")
        times = pd.to_datetime(ds_e5["valid_time"].values)
        tp_mm = ds_e5["tp"].values * 1000.0
        tmap = {ts: idx for idx, ts in enumerate(times)}
        raw_a = np.zeros((len(times), len(ubigeos)), dtype=np.float64)
        for u_idx, ub in enumerate(ubigeos):
            g = w_e5[w_e5["ubigeo"] == ub]
            raw_a[:, u_idx] = tp_mm[:, g["i"].values.astype(int), g["j"].values.astype(int)] @ g["w_area"].values
        ds_e5.close()
        e5_p_rows = []
        for yr in (2023, 2024, 2025):
            for mo in range(1, 13):
                tag = f"{yr}.{mo:02d}.3"
                acc = np.zeros(len(ubigeos), dtype=np.float64)
                ok = True
                for day in range(11, 16):
                    d = pd.Timestamp(year=yr, month=mo, day=day)
                    t05, t00_1, t05_1 = d + pd.Timedelta(hours=5), d + pd.Timedelta(days=1), d + pd.Timedelta(days=1, hours=5)
                    if t05 in tmap and t00_1 in tmap and t05_1 in tmap:
                        acc += np.maximum(0.0, raw_a[tmap[t00_1]] - raw_a[tmap[t05]] + raw_a[tmap[t05_1]])
                    else:
                        ok = False
                if ok:
                    for u_idx, ub in enumerate(ubigeos):
                        e5_p_rows.append((tag, ub, float(acc[u_idx])))
        e5_p = pd.DataFrame(e5_p_rows, columns=["pentad", "ubigeo", "e5_lima_area"])
        mp3 = ch_p.merge(pi_p, on=["pentad", "ubigeo"]).merge(e5_p, on=["pentad", "ubigeo"])
        print(f"\n=== 3c. FULL 3-YEAR SEASONAL CYCLE (36 monthly pentads, Jan 2023-Dec 2025, n={len(mp3):,}) ===")
        print(
            f"  Mean mm/pentad: CHIRPS={mp3['chirps_area'].mean():.2f}, ERA5-Land={mp3['e5_lima_area'].mean():.2f}, PISCOp={mp3['piscop_area'].mean():.2f}"
        )
        for a, b in [("chirps_area", "piscop_area"), ("e5_lima_area", "piscop_area"), ("chirps_area", "e5_lima_area")]:
            d = mp3[a] - mp3[b]
            print(
                f"  {a:14s} vs {b:12s}: bias={d.mean():+6.2f}, MAE={d.abs().mean():5.2f}, RMSE={np.sqrt((d**2).mean()):5.2f}, r={mp3[a].corr(mp3[b]):.4f}"
            )
        mp3z = mp3.merge(diag_e5, on="ubigeo")
        mp3z["zone"] = np.where(mp3z["prov"].isin(["AYABACA", "HUANCABAMBA"]), "Andean (Ayabaca/Huancabamba)", mp3z["dep"])
        print("  By zone (36 monthly pentads, 2023-2025):")
        for z, grp in mp3z.groupby("zone"):
            print(
                f"    {z:30s}: CHIRPS={grp['chirps_area'].mean():5.2f}, E5={grp['e5_lima_area'].mean():5.2f}, "
                f"PISCOp={grp['piscop_area'].mean():5.2f}, r(CH,PI)={grp['chirps_area'].corr(grp['piscop_area']):.3f}, "
                f"r(E5,PI)={grp['e5_lima_area'].corr(grp['piscop_area']):.3f}"
            )

    # 4. Post-2022 -9999 IR gap audit across all daily & pentad Peru NetCDFs
    all_daily_final = sorted(CHIRPS_DIR.glob("chirps_v3_final_sat_202*.nc"))
    if all_daily_final:
        audit_neg9999_gaps(all_daily_final)
    all_daily_prelim = sorted(CHIRPS_DIR.glob("chirps_v3_prelim_sat_202*.nc"))
    if all_daily_prelim:
        print("\n--- Also auditing prelim/sat 2026 daily files for -9999 gaps ---")
        audit_neg9999_gaps(all_daily_prelim)
    # Audit all 66 pentads across Jan 2023 - Oct 2026
    pent_audit_files = [p for p in [p2325_path, pent_path] if p.exists()]
    if pent_audit_files:
        print("\n--- Also auditing 66 LatAm pentads (Jan 2023 - Oct 2026) for -9999 gaps ---")
        g_all = gpd.read_file(GPKG_PATH)
        g_all["ubigeo"] = g_all["ubigeo"].astype(str).str.zfill(6)
        peru_union = g_all.geometry.union_all()
        pilot_union = g_all[g_all["ubigeo"].str[:2].isin({"14", "20", "24"})].geometry.union_all()
        ds0 = xr.open_dataset(pent_audit_files[0], mask_and_scale=False)
        lats, lons = ds0["latitude"].values, ds0["longitude"].values
        ds0.close()
        flip = bool(lats[0] < lats[-1])
        lats_ns = lats[::-1] if flip else lats
        tr = from_origin(float(lons[0]) - 0.025, float(lats_ns[0]) + 0.025, 0.05, 0.05)
        shape = (len(lats_ns), len(lons))
        in_peru = ~geometry_mask([peru_union], out_shape=shape, transform=tr, invert=False)
        in_pilot = ~geometry_mask([pilot_union], out_shape=shape, transform=tr, invert=False)
        stacks = []
        ever_valid = np.zeros(shape, dtype=bool)
        for p in pent_audit_files:
            ds = xr.open_dataset(p, mask_and_scale=False)
            for v in ds.data_vars:
                arr = ds[v].values
                if flip:
                    arr = arr[:, ::-1, :]
                ever_valid |= np.any(arr >= 0, axis=0)
                stacks.append((f"{p.name}:{v}", ds["pentad"].values, arr))
            ds.close()
        peru_land = in_peru & ever_valid
        pilot_land = in_pilot & ever_valid
        for label, ptags, arr in stacks:
            n_tot = len(ptags)
            n_pg_pents = 0
            n_pl_pents = 0
            tot_pg_cells = 0
            tot_pl_cells = 0
            hits = []
            for idx_p, pt in enumerate(ptags):
                is_gap = (arr[idx_p] < -9000) | np.isnan(arr[idx_p])
                c_pg = int((is_gap & peru_land).sum())
                c_pl = int((is_gap & pilot_land).sum())
                if c_pg > 0:
                    n_pg_pents += 1
                    tot_pg_cells += c_pg
                    hits.append((str(pt), c_pg, c_pl))
                if c_pl > 0:
                    n_pl_pents += 1
                    tot_pl_cells += c_pl
            print(
                f"  {label}: {n_pg_pents}/{n_tot} pentads with Peru land -9999 "
                f"({tot_pg_cells:,} cell-pentads = {100*tot_pg_cells/(n_tot*int(peru_land.sum())):.5f}%), "
                f"pilot: {n_pl_pents}/{n_tot} ({tot_pl_cells} cell-pentads)"
            )
            if hits:
                print("    Examples:", hits[:8])


if __name__ == "__main__":
    main()
