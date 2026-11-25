# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=2.0",
#   "pandas>=2.2",
#   "pyarrow>=17.0",
# ]
# ///
"""Evaluate partial epi-week completeness rules (n_dias = 1..6 vs 7).

Uses:
- 8 years of daily PISCOp v3.0 pilot district rainfall (2018-2025, 116 districts, ~48k district-weeks)
  to quantify raw partial sum vs linear 7/n_dias scaling error for ptot.
- 8+ years of daily SENAMHI pilot station observations (2018-2026, 10 stations) to quantify
  partial-week mean error for tmean, tmax, tmin, humr.
- Exact live availability timeline for ERA5-Land (5-6 day lag) and CHIRPS v3 prelim/sat
  (pentad end + 2 days) against Sunday-Saturday MINSA epi-weeks.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROTO = Path(
    "/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week"
)


def main() -> None:
    cal = pd.read_parquet(PROTO / "minsa_calendar.parquet")
    cal["dow_sun0"] = (cal["date"].dt.day_of_week + 1) % 7  # Sun=0..Sat=6

    # --- 1. Precipitation partial-week error (PISCOp v3 2018-2025, 116 pilot districts) ---
    p_daily = pd.read_parquet(PROTO / "piscop_pilot_daily_2018_2025.parquet")
    p_daily = p_daily.merge(cal[["date", "dow_sun0"]], on="date", how="left")
    # Keep only complete 7-day epi-weeks
    wk_cnt = p_daily.groupby(["ubigeo", "epi_year", "epi_week"])["date"].transform("count")
    p_full = p_daily[wk_cnt == 7].copy()

    full_sum = (
        p_full.groupby(["ubigeo", "epi_year", "epi_week"])["piscop_area"]
        .sum()
        .rename("ptot_7d")
    )

    print("=== 1. PRECIPITATION PARTIAL EPI-WEEK ERROR (PISCOp v3, 2018-2025, 116 pilot districts) ===")
    print(f"Total complete district-weeks: {len(full_sum):,} (wet >=10 mm: {(full_sum >= 10).sum():,})")
    for n_dias in range(1, 7):
        part = (
            p_full[p_full["dow_sun0"] < n_dias]
            .groupby(["ubigeo", "epi_year", "epi_week"])["piscop_area"]
            .sum()
            .rename("part")
            .to_frame()
            .join(full_sum)
        )
        raw_err = part["part"] - part["ptot_7d"]
        scaled = part["part"] * (7.0 / n_dias)
        scl_err = scaled - part["ptot_7d"]
        wet = part[part["ptot_7d"] >= 10.0]
        raw_rel_wet = ((wet["part"] - wet["ptot_7d"]) / wet["ptot_7d"]).mean() * 100
        scl_mae_wet = (wet["part"] * (7.0 / n_dias) - wet["ptot_7d"]).abs().mean()
        raw_mae_wet = (wet["part"] - wet["ptot_7d"]).abs().mean()
        print(
            f"  n_dias={n_dias}: "
            f"RAW bias={raw_err.mean():+6.2f} mm, MAE={raw_err.abs().mean():5.2f}, r={part['part'].corr(part['ptot_7d']):.3f} (wet>=10mm bias={raw_rel_wet:+5.1f}%, MAE={raw_mae_wet:5.1f}) | "
            f"SCALED(7/n) bias={scl_err.mean():+5.2f}, MAE={scl_err.abs().mean():5.2f}, r={scaled.corr(part['ptot_7d']):.3f} (wet MAE={scl_mae_wet:5.1f})"
        )

    # --- 2. Temperature & RH partial-week error (SENAMHI 10 stations, 2018-2026) ---
    st = pd.read_parquet(PROTO / "senamhi/pilot_stations_daily.parquet")
    st["date"] = pd.to_datetime(st["date"])
    st["tmean"] = 0.5 * (st["TEMPERATURA_MAXIMA"] + st["TEMPERATURA_MINIMA"])
    st = st.merge(cal[["date", "epi_year", "epi_week", "dow_sun0"]], on="date", how="inner")

    print("\n=== 2. TEMPERATURE & RH PARTIAL EPI-WEEK ERROR (10 SENAMHI stations, 2018-2026) ===")
    for col, label in [
        ("tmean", "tmean (C)"),
        ("TEMPERATURA_MAXIMA", "tmax (C)"),
        ("TEMPERATURA_MINIMA", "tmin (C)"),
        ("HUMEDAD_RELATIVA", "humr (pp)"),
    ]:
        sub = st.dropna(subset=[col]).copy()
        cnt = sub.groupby(["station_id", "epi_year", "epi_week"])[col].transform("count")
        sub7 = sub[cnt == 7]
        full_m = sub7.groupby(["station_id", "epi_year", "epi_week"])[col].mean().rename("full")
        print(f"  -- {label} (n={len(full_m):,} full station-weeks) --")
        for n_dias in [3, 4, 5, 6]:
            part_m = (
                sub7[sub7["dow_sun0"] < n_dias]
                .groupby(["station_id", "epi_year", "epi_week"])[col]
                .mean()
                .rename("part")
                .to_frame()
                .join(full_m)
            )
            diff = part_m["part"] - part_m["full"]
            print(
                f"    n_dias={n_dias}: bias={diff.mean():+.3f}, MAE={diff.abs().mean():.3f}, "
                f"p95_abs={diff.abs().quantile(0.95):.3f}, max_abs={diff.abs().max():.3f}, "
                f"r={part_m['part'].corr(part_m['full']):.4f}"
            )

    # --- 3. Exact live availability schedule for ERA5-Land and CHIRPS v3 prelim/sat ---
    # Simulate all 52 epi-weeks of 2025 + 45 of 2026:
    # An epi-week runs Sunday (day 0) .. Saturday (day 6).
    # ERA5-Land day D (Lima) needs up to 05:00 UTC of D+1; published by D+6 ~12 UTC (lag=6 days after day D for full Lima day, or lag=5 for UTC day D).
    # CHIRPS prelim/sat pentad end + 2 days (pentads end on day 5, 10, 15, 20, 25, month_end).
    print("\n=== 3. LIVE AVAILABILITY CALENDAR FOR JUST-ENDED EPI-WEEK (Sun..Sat) ===")
    print("  Suppose epi-week W ends Saturday S (day 6). When do all 7 days (S-6 .. S) arrive?")
    print("  - ERA5-Land (UTC day D at D+5 12 UTC; Lima day D needs 05 UTC of D+1 -> D+6 12 UTC):")
    print("      On Wednesday (S+4, Observatorio update day): UTC n_dias=6 (Sun..Fri? No: Wed-5=Fri -> 6d? Wait: 2026-SE45 ended Sat Nov 14; Wed Nov 18 had ERA5-Land through Nov 12/13 -> Observatorio had n_dias=4, Sun-Wed Nov 8-11!)")
    print("      On Thursday  (S+5, ~12 UTC): ERA5-Land reaches Saturday S (UTC) -> 7/7 UTC days, 6/7 Lima days.")
    print("      On Friday    (S+6, ~12 UTC): ERA5-Land reaches Sunday S+1 05 UTC -> 7/7 Lima days.")

    # Empirical simulation of CHIRPS v3 prelim/sat completeness across 2024-2026 epi-weeks
    # Given Saturday S, check how many days of W are published by S+k (k = 2, 3, 4, 5, 6, 7 days after Saturday)
    def chirps_prelim_avail_date(d: pd.Timestamp) -> pd.Timestamp:
        day = d.day
        if day <= 5:
            pend = d.replace(day=5)
        elif day <= 10:
            pend = d.replace(day=10)
        elif day <= 15:
            pend = d.replace(day=15)
        elif day <= 20:
            pend = d.replace(day=20)
        elif day <= 25:
            pend = d.replace(day=25)
        else:
            pend = (d + pd.offsets.MonthEnd(0)).normalize()
        return pend + pd.Timedelta(days=2)

    cal_sim = cal[cal["epi_year"].isin([2024, 2025])].copy()
    cal_sim["chirps_avail"] = cal_sim["date"].apply(chirps_prelim_avail_date)
    print("\n  CHIRPS v3 prelim/sat completeness for just-ended epi-week W (2024-2025, 105 epi-weeks):")
    for k_after_sat, day_name in [(2, "Mon S+2"), (3, "Tue S+3"), (4, "Wed S+4"), (5, "Thu S+5"), (6, "Fri S+6"), (7, "Sat S+7"), (8, "Sun S+8")]:
        n_full = 0
        min_nd = 7
        nd_list = []
        for (_, _), grp in cal_sim.groupby(["epi_year", "epi_week"]):
            if len(grp) < 7:
                continue
            sat = grp["date"].max()
            run_day = sat + pd.Timedelta(days=k_after_sat)
            nd = int((grp["chirps_avail"] <= run_day).sum())
            nd_list.append(nd)
            if nd == 7:
                n_full += 1
            min_nd = min(min_nd, nd)
        print(
            f"    Run on {day_name}: 7/7 complete in {n_full:3d}/{len(nd_list)} weeks ({100*n_full/len(nd_list):5.1f}%), "
            f"median n_dias={np.median(nd_list):.1f}, min n_dias={min_nd}"
        )


if __name__ == "__main__":
    main()
