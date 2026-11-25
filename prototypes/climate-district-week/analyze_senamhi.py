# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "netcdf4>=1.7",
#   "numpy>=2.0",
#   "pandas>=2.2",
#   "pyarrow>=17.0",
#   "xarray>=2024.10",
# ]
# ///
"""Validate ERA5-Land district epi-week temperatures against 10 SENAMHI stations (2018-2026).

Evaluates:
1. Long-term (2018-2026, 254-444 epi-weeks per station) agreement between SENAMHI station
   weekly temperatures and CDC Observatorio (ERA5-Land area mean): raw r, deseasonalized
   anomaly r, week-to-week delta r, and constant offset across urban, coastal ocean-masked,
   and Andean (Ayabaca, Huancabamba) stations.
2. Direct comparison of our own ERA5-Land hourly aggregations (area vs population-weighted
   vs nearest-land-reassigned population vs station-pixel value) against the 10 SENAMHI
   stations during March 2023 and July 2024 (when available).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

PROTO = Path(
    "/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week"
)


def main() -> None:
    cal = pd.read_parquet(PROTO / "minsa_calendar.parquet")
    obs = pd.read_parquet(PROTO / "observatorio_pilot.parquet")
    st_daily = pd.read_parquet(PROTO / "senamhi/pilot_stations_daily.parquet")
    st_meta = pd.read_parquet(PROTO / "senamhi/stations_meta.parquet")
    diag_e5 = pd.read_parquet(PROTO / "weights/diag_era5_land.parquet").set_index("ubigeo")

    st_daily["date"] = pd.to_datetime(st_daily["date"])
    st_daily = st_daily.merge(cal, on="date", how="inner")
    st_daily["tmean_mid"] = 0.5 * (
        st_daily["TEMPERATURA_MAXIMA"] + st_daily["TEMPERATURA_MINIMA"]
    )

    wk = (
        st_daily.groupby(["station_id", "ubigeo", "epi_year", "epi_week"])
        .agg(
            n_tmean=("tmean_mid", "count"),
            n_tmax=("TEMPERATURA_MAXIMA", "count"),
            n_tmin=("TEMPERATURA_MINIMA", "count"),
            st_tmean=("tmean_mid", "mean"),
            st_tmax=("TEMPERATURA_MAXIMA", "mean"),
            st_tmin=("TEMPERATURA_MINIMA", "mean"),
            st_humr=("HUMEDAD_RELATIVA", "mean"),
            week_start=("date", "min"),
        )
        .reset_index()
    )

    m = wk.merge(
        obs[["ubigeo", "epi_year", "epi_week", "tmean", "tmax", "tmin", "humr", "n_dias"]],
        on=["ubigeo", "epi_year", "epi_week"],
        how="inner",
    )
    m = m[m["n_dias"] == 7]

    meta_map = st_meta.set_index("station_id").to_dict("index")
    summary_rows = []

    print("=== 1. SENAMHI STATIONS vs ERA5-LAND / OBSERVATORIO (2018-2026, >=6 station days/wk) ===")
    for sid, grp in m.groupby("station_id"):
        info = meta_map[sid]
        ub = info["ubigeo"]
        d = diag_e5.loc[ub]
        g = grp[grp["n_tmean"] >= 6].dropna(subset=["st_tmean", "tmean"]).sort_values("week_start").copy()
        # Consecutive 7-day week-to-week deltas only
        g["gap_days"] = g["week_start"].diff().dt.days
        g["d_st"] = g["st_tmean"].diff()
        g["d_ob"] = g["tmean"].diff()
        g_consec = g[g["gap_days"] == 7]

        # Deseasonalized anomalies (minus station/district week-of-year mean)
        g["anom_st"] = g["st_tmean"] - g.groupby("epi_week")["st_tmean"].transform("mean")
        g["anom_ob"] = g["tmean"] - g.groupby("epi_week")["tmean"].transform("mean")

        gx = grp[grp["n_tmax"] >= 6].dropna(subset=["st_tmax", "tmax"])
        gn = grp[grp["n_tmin"] >= 6].dropna(subset=["st_tmin", "tmin"])

        row = {
            "station_id": sid,
            "name": info["name"],
            "ubigeo": ub,
            "role": info["role"],
            "alt_m": info["altitude_m"],
            "valid_area_frac": d["valid_area_frac"],
            "valid_pop_frac": d["valid_pop_frac"],
            "n_weeks": len(g),
            "n_consec_pairs": len(g_consec),
            "r_tmean": g["st_tmean"].corr(g["tmean"]),
            "r_anom": g["anom_st"].corr(g["anom_ob"]),
            "r_delta": g_consec["d_st"].corr(g_consec["d_ob"]),
            "r_tmax": gx["st_tmax"].corr(gx["tmax"]),
            "r_tmin": gn["st_tmin"].corr(gn["tmin"]),
            "bias_tmean_c": (g["tmean"] - g["st_tmean"]).mean(),
            "bias_tmax_c": (gx["tmax"] - gx["st_tmax"]).mean(),
            "bias_tmin_c": (gn["tmin"] - gn["st_tmin"]).mean(),
            "rmse_anom_c": float(np.sqrt(((g["anom_ob"] - g["anom_st"]) ** 2).mean())),
        }
        summary_rows.append(row)
        print(
            f"  {sid} {info['name']:15s} ({ub}, {info['altitude_m']:4.0f}m, landA={d['valid_area_frac']:.2f}, n={len(g):3d}w): "
            f"r={row['r_tmean']:.3f}, r_anom={row['r_anom']:.3f}, r_dw={row['r_delta']:.3f}, "
            f"r_tx={row['r_tmax']:.3f}, r_tn={row['r_tmin']:.3f}, bias={row['bias_tmean_c']:+.2f}C, anom_RMSE={row['rmse_anom_c']:.2f}C"
        )

    out_df = pd.DataFrame(summary_rows)
    out_df.to_parquet(PROTO / "senamhi_validation_summary.parquet", index=False)

    # --- 2. Direct check against our hourly ERA5-Land sample (area vs pop vs station cell) ---
    hr_path = PROTO / "hourly_experiment_results.parquet"
    if hr_path.exists():
        hr = pd.read_parquet(hr_path)
        hr_lima = hr[hr["tz"] == "lima"].pivot(
            index=["ubigeo", "epi_year", "epi_week"],
            columns="scheme",
            values=["tmean", "tmax_mean", "tmin_mean"],
        )
        hr_lima.columns = [f"{a}_{b}" for a, b in hr_lima.columns]
        hr_lima = hr_lima.reset_index()
        m2 = wk.merge(hr_lima, on=["ubigeo", "epi_year", "epi_week"], how="inner")
        m2 = m2[m2["n_tmean"] >= 6]
        print(f"\n=== 2. SENAMHI vs OUR HOURLY ERA5-LAND (n={len(m2)} station-weeks) ===")
        for sid, grp in m2.groupby("station_id"):
            info = meta_map[sid]
            print(
                f"  {sid} {info['name']:15s} (n={len(grp)}w): "
                f"station={grp['st_tmean'].mean():.2f}C | "
                f"E5 area={grp['tmean_area'].mean():.2f} ({(grp['tmean_area']-grp['st_tmean']).mean():+.2f}) | "
                f"E5 pop={grp['tmean_pop'].mean():.2f} ({(grp['tmean_pop']-grp['st_tmean']).mean():+.2f}) | "
                f"E5 popR={grp['tmean_pop_reassigned'].mean():.2f} ({(grp['tmean_pop_reassigned']-grp['st_tmean']).mean():+.2f})"
            )


if __name__ == "__main__":
    main()
