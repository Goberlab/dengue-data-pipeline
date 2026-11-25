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
"""Compute area-weighted, population-weighted (GHS-POP R2023A 3ss), and
cell-centroid spatial aggregation weights for all 116 pilot districts.

Outputs parquet weight tables under:
  data/prototypes/climate-district-week/weights/
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.merge import merge as rio_merge
from shapely.geometry import Point, box

MAIN_DATA = Path("/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data")
PROTO_DIR = MAIN_DATA / "prototypes/climate-district-week"
GPKG_PATH = MAIN_DATA / "raw/inei-ide-distrito/DISTRITO.gpkg"
GHSPOP_DIR = PROTO_DIR / "ghspop"
OUT_DIR = PROTO_DIR / "weights"

PILOT_DEPS = {"14", "20", "24"}


def load_pilot_districts() -> gpd.GeoDataFrame:
    g = gpd.read_file(GPKG_PATH)
    g["ubigeo"] = g["ubigeo"].astype(str).str.zfill(6)
    pilot = g[g["ubigeo"].str[:2].isin(PILOT_DEPS)].copy()
    pilot = pilot.sort_values("ubigeo").reset_index(drop=True)
    return pilot


def mosaic_ghspop_pilot(pilot_bounds: tuple[float, float, float, float]) -> Path:
    mosaic_path = GHSPOP_DIR / "ghspop_e2020_3ss_pilot.tif"
    if mosaic_path.exists():
        return mosaic_path
    tifs = sorted(GHSPOP_DIR.glob("GHS_POP_E2020_GLOBE_R2023A_4326_3ss_V1_0_R10_C1*.tif"))
    srcs = [rasterio.open(p) for p in tifs]
    minx, miny, maxx, maxy = pilot_bounds
    arr, out_trans = rio_merge(srcs, bounds=(minx - 0.2, miny - 0.2, maxx + 0.2, maxy + 0.2))
    meta = srcs[0].meta.copy()
    meta.update(
        driver="GTiff",
        height=arr.shape[1],
        width=arr.shape[2],
        transform=out_trans,
        compress="deflate",
    )
    for s in srcs:
        s.close()
    with rasterio.open(mosaic_path, "w", **meta) as dst:
        dst.write(arr)
    return mosaic_path


def build_grid_weights(
    pilot_4326: gpd.GeoDataFrame,
    lats: np.ndarray,
    lons: np.ndarray,
    valid_mask: np.ndarray,
    pop_tif: Path,
    grid_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build exact area, population, and centroid weights for a regular lat/lon grid."""
    dlat = float(np.median(np.abs(np.diff(lats))))
    dlon = float(np.median(np.abs(np.diff(lons))))

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
                    "geometry": box(lon - dlon / 2, lat - dlat / 2, lon + dlon / 2, lat + dlat / 2),
                }
            )
    grid_4326 = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    grid_utm = grid_4326.to_crs(epsg=32717)
    pilot_utm = pilot_4326.to_crs(epsg=32717)

    # Precompute valid cell center points in UTM for nearest fallback
    valid_cells_utm = grid_utm[grid_utm["is_valid"]].copy()
    valid_centers_utm = gpd.GeoSeries(
        [Point(r["lon"], r["lat"]) for _, r in valid_cells_utm.iterrows()], crs="EPSG:4326"
    ).to_crs(epsg=32717)
    valid_cells_utm["center_utm"] = valid_centers_utm.values

    pop_src = rasterio.open(pop_tif)
    nodata = pop_src.nodata

    def pop_in_geom(geom_4326) -> float:
        if geom_4326.is_empty:
            return 0.0
        try:
            out, _ = rio_mask(pop_src, [geom_4326], crop=True, all_touched=False)
        except ValueError:
            return 0.0
        data = out[0].astype(np.float64)
        if nodata is not None:
            data = np.where(data == nodata, 0.0, data)
        data = np.where(np.isnan(data) | (data < 0), 0.0, data)
        return float(data.sum())

    weight_rows: list[dict] = []
    diag_rows: list[dict] = []

    for idx_row, d_utm in pilot_utm.iterrows():
        d_4326 = pilot_4326.loc[idx_row]
        ubigeo = d_utm["ubigeo"]
        geom_utm = d_utm.geometry
        geom_4326 = d_4326.geometry
        dist_area = float(geom_utm.area)
        dist_pop = pop_in_geom(geom_4326)

        ov_idx = grid_utm.index[grid_utm.intersects(geom_utm)].tolist()
        ov_utm = grid_utm.loc[ov_idx].copy()
        ov_4326 = grid_4326.loc[ov_idx]

        inter_areas = []
        inter_pops = []
        center_in_flags = []
        for k in ov_idx:
            g_inter_utm = grid_utm.at[k, "geometry"].intersection(geom_utm)
            inter_areas.append(float(g_inter_utm.area))
            g_inter_4326 = ov_4326.at[k, "geometry"].intersection(geom_4326)
            inter_pops.append(pop_in_geom(g_inter_4326))
            c_pt = (
                gpd.GeoSeries([Point(grid_4326.at[k, "lon"], grid_4326.at[k, "lat"])], crs="EPSG:4326")
                .to_crs(epsg=32717)
                .iloc[0]
            )
            center_in_flags.append(bool(geom_utm.contains(c_pt)))

        ov_utm["inter_area"] = inter_areas
        ov_utm["inter_pop"] = inter_pops
        ov_utm["center_in"] = center_in_flags

        valid_ov = ov_utm[ov_utm["is_valid"]].copy()
        valid_area_sum = float(valid_ov["inter_area"].sum())
        valid_pop_sum = float(valid_ov["inter_pop"].sum())
        valid_centers_sum = int(valid_ov["center_in"].sum())

        # Determine nearest valid cell to district centroid (and pop-weighted centroid if available)
        dist_centroid_utm = geom_utm.centroid
        dists = valid_cells_utm["center_utm"].distance(dist_centroid_utm)
        nearest_k = int(dists.idxmin())
        nearest_dist_km = float(dists.min() / 1000.0)

        used_area_fallback = valid_area_sum <= 0
        used_pop_fallback = valid_pop_sum <= 0
        used_center_fallback = valid_centers_sum == 0

        # Emit normalized weights for all intersecting valid cells (plus nearest if fallback needed)
        target_rows = valid_ov.copy()
        if used_area_fallback or used_center_fallback or used_pop_fallback:
            if nearest_k not in target_rows.index:
                nr = grid_utm.loc[[nearest_k]].copy()
                nr["inter_area"] = 0.0
                nr["inter_pop"] = 0.0
                nr["center_in"] = False
                target_rows = pd.concat([target_rows, nr])

        for k, r in target_rows.iterrows():
            w_area = (
                (1.0 if k == nearest_k else 0.0)
                if used_area_fallback
                else float(r["inter_area"]) / valid_area_sum
            )
            if used_pop_fallback:
                # Fall back to area weight when 0 population falls inside valid land cells
                w_pop = w_area
            else:
                w_pop = float(r["inter_pop"]) / valid_pop_sum
            w_center = (
                (1.0 if k == nearest_k else 0.0)
                if used_center_fallback
                else (1.0 / valid_centers_sum if r["center_in"] else 0.0)
            )
            if w_area > 0 or w_pop > 0 or w_center > 0:
                weight_rows.append(
                    {
                        "grid": grid_name,
                        "ubigeo": ubigeo,
                        "i": int(r["i"]),
                        "j": int(r["j"]),
                        "lat": float(r["lat"]),
                        "lon": float(r["lon"]),
                        "w_area": w_area,
                        "w_pop": w_pop,
                        "w_center": w_center,
                    }
                )

        diag_rows.append(
            {
                "grid": grid_name,
                "ubigeo": ubigeo,
                "dep": d_utm["nombdep"],
                "prov": d_utm["nombprov"],
                "dist": d_utm["nombdist"],
                "area_km2": dist_area / 1e6,
                "ghspop_2020": dist_pop,
                "n_touch": len(ov_utm),
                "n_valid_touch": len(valid_ov),
                "n_valid_centers": valid_centers_sum,
                "valid_area_frac": valid_area_sum / dist_area if dist_area > 0 else 0.0,
                "valid_pop_frac": valid_pop_sum / dist_pop if dist_pop > 0 else np.nan,
                "used_area_fallback": used_area_fallback,
                "used_pop_fallback": used_pop_fallback,
                "used_center_fallback": used_center_fallback,
                "nearest_valid_km": nearest_dist_km,
            }
        )

    pop_src.close()
    return pd.DataFrame(weight_rows), pd.DataFrame(diag_rows)


def main() -> None:
    import xarray as xr

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pilot = load_pilot_districts()
    pop_tif = mosaic_ghspop_pilot(tuple(pilot.total_bounds))
    print(f"GHS-POP pilot mosaic ready: {pop_tif.name} ({pop_tif.stat().st_size / 1e6:.2f} MB)")

    # 1. ERA5-Land 0.1 deg grid
    ds_e5 = xr.open_dataset(PROTO_DIR / "era5land_hourly_test_20240315.nc")
    e5_mask = ~np.isnan(ds_e5["t2m"].isel(valid_time=0).values)
    w_e5, d_e5 = build_grid_weights(
        pilot, ds_e5["latitude"].values, ds_e5["longitude"].values, e5_mask, pop_tif, "era5_land"
    )
    ds_e5.close()
    w_e5.to_parquet(OUT_DIR / "weights_era5_land.parquet", index=False)
    d_e5.to_parquet(OUT_DIR / "diag_era5_land.parquet", index=False)

    print("\n=== ERA5-Land pilot spatial mask & population coverage ===")
    print(f"Total pilot GHS-POP 2020: {d_e5['ghspop_2020'].sum():,.0f}")
    print("Districts with valid_area_frac < 0.99:", int((d_e5["valid_area_frac"] < 0.99).sum()))
    print("Districts with valid_pop_frac < 0.95:", int((d_e5["valid_pop_frac"] < 0.95).sum()))
    print("Districts with valid_pop_frac == 0 (pop fallback):", int(d_e5["used_pop_fallback"].sum()))
    print("Districts with 0 valid cell centers:", int(d_e5["used_center_fallback"].sum()))
    print("\nLowest 15 valid_pop_frac districts (ERA5-Land):")
    cols = ["ubigeo", "dep", "dist", "ghspop_2020", "valid_area_frac", "valid_pop_frac", "n_valid_touch", "n_valid_centers"]
    print(d_e5.sort_values("valid_pop_frac").head(15)[cols].to_string(index=False))

    # 2. PISCOp v3.0 0.1 deg grid (slice to pilot bbox)
    ds_p = xr.open_dataset(PROTO_DIR / "PISCOp_d.nc")
    sub_p = ds_p.sel(latitude=slice(-3.1, -7.5), longitude=slice(-81.6, -78.7))
    p_mask = ~np.isnan(sub_p["precipitation"].isel(Z1=-1).values)
    w_p, d_p = build_grid_weights(
        pilot, sub_p["latitude"].values, sub_p["longitude"].values, p_mask, pop_tif, "piscop_v3"
    )
    ds_p.close()
    w_p.to_parquet(OUT_DIR / "weights_piscop_v3.parquet", index=False)
    d_p.to_parquet(OUT_DIR / "diag_piscop_v3.parquet", index=False)
    print("\n=== PISCOp v3.0 pilot spatial mask ===")
    print("Districts with valid_area_frac < 0.99:", int((d_p["valid_area_frac"] < 0.99).sum()))
    print("Lowest 5 valid_area_frac (PISCOp):", d_p.sort_values("valid_area_frac").head(5)[cols].to_string(index=False))


if __name__ == "__main__":
    main()
