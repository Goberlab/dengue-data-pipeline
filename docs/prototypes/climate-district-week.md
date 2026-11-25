# Turning gridded climate values into district epi-week values

Prototype findings for ticket #24 on the Peru pilot (Piura, Tumbes, Lambayeque: 116 districts, 6-digit UBIGEO). All downloads, scripts, and checks ran on 2026-11-24 and 2026-11-25 against primary upstream archives, CDC Peru Observatorio exports (snapshot `20261123T161922Z`), and SENAMHI's public station API.

All prototype data live outside git under `/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week/`. SENAMHI PISCOp v3.0 (GPL 3.0+) was used strictly as an offline benchmark and never enters git or any panel output.

## Short summary of recommended rules

Every rule below is a recommendation for user sign-off. Each section gives the empirical evidence, the recommended rule, and the main alternative.

| Panel variable | Upstream source | Spatial rule | Time boundary and formula | Live completeness rule |
| --- | --- | --- | --- | --- |
| `tmean` (°C) | ERA5-Land hourly (`reanalysis-era5-land`, `2m_temperature`) | Population-weighted mean using GHS-POP R2023A 3 arc-sec (ocean-masked population reassigned to nearest valid land cell) | `America/Lima` (UTC-5) Sunday to Saturday epi-week; mean of 7 daily means (24 hourly values per day) | Require `n_dias = 7` for final weekly row; emit partial row (`n_dias >= 4`) only if forecast runs before Friday, stamped with `n_dias` and `available_at` |
| `tmax` (°C) | ERA5-Land hourly (`2m_temperature`) | Same as `tmean` | `America/Lima` epi-week; mean of 7 daily maxima (not weekly absolute maximum) | Same as `tmean` |
| `tmin` (°C) | ERA5-Land hourly (`2m_temperature`) | Same as `tmean` | `America/Lima` epi-week; mean of 7 daily minima (not weekly absolute minimum) | Same as `tmean` |
| `humr` (%) | ERA5-Land hourly (`2m_temperature`, `2m_dewpoint_temperature`) | Same as `tmean` | Compute RH hourly over liquid water (Alduchov-Eskridge / Magnus) before averaging to `America/Lima` daily and epi-week means | Same as `tmean` |
| `ptot_chirps` (mm, primary) | CHIRPS v3.0 Daily (`prelim/sat` live, `final/sat` history) | Same population-weighted rule on 0.05° grid (0 ocean-masked pilot districts) | UTC daily sum over the 7 calendar dates of the MINSA epi-week; versioned by `available_at` (preliminary then final) | Require `n_dias = 7` (never emit an unscaled partial sum as weekly `ptot`) |
| `ptot_era5` (mm, optional companion) | ERA5-Land (`total_precipitation` at `00:00` and `05:00` UTC) | Same as `tmean` | `America/Lima` epi-week sum via `tp(D+1, 00:00) - tp(D, 05:00) + tp(D+1, 05:00)` | Require `n_dias = 7` |

Key operational finding from CDS testing (2026-11-24 and 2026-11-25): `derived-era5-land-daily-statistics` sat in `accepted` for over 2 hours for a single day without starting, omits `total_precipitation`, and cannot compute hourly relative humidity. Pull `reanalysis-era5-land` hourly directly (1 month of 3 variables for the pilot took 13 to 28 minutes and weighed 3.8 to 4.5 MB; a full year of 2-hour `total_precipitation` took 3 to 11 minutes and weighed 1.6 to 1.8 MB).

## 1. Spatial aggregation: area mean versus population-weighted mean

### Gridded population source

We evaluated two 100 m CC BY 4.0 gridded population sources on 2026-11-24:

- **GHS-POP R2023A (3 arc-seconds, ~92 m in Peru, WGS84, European Commission JRC, `doi:10.2760/098587`)**: licensed **CC BY 4.0**, covers **1975 to 2030 at 5-year epochs** (`2000, 2005, 2010, 2015, 2020, 2025, 2030`), direct HTTPS tiles from `jeodpp.jrc.ec.europa.eu` (pilot covered by tiles `R10_C10` and `R10_C11`, 38 MB unzipped; 6.99 MB clipped mosaic; 2020 pilot sum = 3,507,471).
- **WorldPop R2025A Peru Constrained 100 m (`2015 to 2030`)**: licensed **CC BY 4.0**, hosted at `data.worldpop.org` (56.6 MB per year). Direct downloads stalled repeatedly (`< 1 KB/s` and timeouts) on 2026-11-24, and coverage begins in 2015 rather than 2000.

We used **GHS-POP R2023A 3 arc-sec (`E2020`)** for all prototype weights. A sensitivity check comparing **`E2020` versus `E2000`** weights across all 116 pilot districts (March 2023 ERA5-Land temperature, computed 2026-11-25) shows negligible drift over 20 years: mean `-0.001 °C`, MAE **`0.010 °C`**, p95 `0.031 °C`, max `0.139 °C` (Chulucanas `200401`). Because weights barely move over two decades, using a fixed pre-period or single static epoch (or 5-year epochs gated by `available_at`) introduces practically zero leakage or discontinuity.

### Coastal ocean masking and small districts on ERA5-Land (0.1°)

Intersecting INEI IDE `DISTRITO.gpkg` (116 pilot districts, EPSG:4326, area computed in EPSG:32717) with the ERA5-Land 0.1° land-sea mask (`era5land_hourly_test_20240315.nc`, checked 2026-11-24) reveals two major failure modes for naive aggregation:

1. **Cell-center-in-polygon fails on 30 of 116 pilot districts (25.9%)**: 30 districts contain zero ERA5-Land land cell centers, including major urban dengue districts such as Chiclayo (`140101`), Veintiseis de Octubre (`200115`), Jose Leonardo Ortiz (`140105`), and Bellavista (`200602`, 2.16 km²). Nationally (`DISTRITO.gpkg`, 1,890 districts, UTM 18S), **625 districts (33.1%)** are smaller than one 0.1° ERA5-Land cell (~123 km²) and **147 districts (7.8%)** are smaller than one 0.05° CHIRPS cell (~31 km²), with a minimum area of 0.79 km². Falling back to the single nearest cell introduces jumps of up to **3.21 °C** relative to exact polygon overlap (`MAE = 0.21 °C`, `p95 = 0.75 °C` across 696 pilot district-weeks in March 2023 and July 2024).
2. **Partial ocean masking hits 28 of 116 pilot districts (24.1%)**: All 116 pilot districts touch at least 1 valid ERA5-Land land cell (`min = 1`), so zero pilot districts have 0% land overlap. However, several coastal districts lose nearly all of their area or populated coastal towns to the ocean mask:

| UBIGEO | District | Area (km²) | Valid land area share | Valid land population share (GHS-POP 2020) | Valid land cells touching | Valid centers inside |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `140114` | Santa Rosa (Chiclayo) | 13.6 | 0.43% | 0.009% | 1 | 0 |
| `140104` | Eten Puerto (Chiclayo) | 13.2 | 6.68% | 0.88% | 1 | 0 |
| `140108` | Monsefu (Chiclayo) | 46.8 | 37.61% | 18.63% | 3 | 0 |
| `240101` | Tumbes (Tumbes) | 151.4 | 52.13% | 97.71% | 3 | 1 |
| `240301` | Zarumilla (Zarumilla) | 112.4 | 60.54% | 99.52% | 3 | 1 |
| `140103` | Eten (Chiclayo) | 83.2 | 66.56% | 18.29% | 1 | 1 |
| `140311` | San Jose (Lambayeque) | 45.5 | 76.76% | 43.14% | 3 | 0 |
| `240103` | La Cruz (Tumbes) | 64.5 | 77.57% | 0.33% | 3 | 0 |
| `200504` | Colan (Paita) | 122.3 | 78.02% | 86.06% | 4 | 1 |
| `200704` | Lobitos (Talara) | 237.2 | 82.74% | 13.50% | 6 | 1 |
| `240201` | Zorritos (Contralmirante Villar) | 647.1 | 87.71% | 7.37% | 8 | 6 |

Nationally, an audit of CDC Observatorio 2026 exports (`20261123T161922Z`, checked 2026-11-25) shows **13 coastal districts** with `tmean = NaN` across all 45 epi-weeks of 2026 (Callao: Bellavista, La Perla, La Punta; Lambayeque: Eten Puerto `140104`; Lima: Brena, Chorrillos, Magdalena del Mar, Pueblo Libre, Pucusana, San Miguel, Santa Maria del Mar, Caleta de Carquin, Hualmay). Any national pipeline rule must therefore include an explicit nearest-valid-land-cell fallback whenever a district has zero valid land overlap or ocean-masked coastal population.

By contrast, on **CHIRPS v3.0 (0.05°)**, **0 of 116 pilot districts** suffer ocean masking (`valid_area_frac = 1.000` for every pilot district, checked 2026-11-25). On **PISCOp v3.0 (0.1°)**, 6 pilot districts have partial boundary masking (`min = 69.9%` in Morrope, `valid_pop_frac >= 99.7%` everywhere).

### Area mean versus population-weighted mean (stress tests)

Across 6 complete epi-weeks of hourly ERA5-Land (`2023-SE10..SE12` Cyclone Yaku wet summer + `2024-SE28..SE30` cool dry winter; 696 district-weeks, `America/Lima`, computed 2026-11-25):

- **Pilot-wide difference (`pop - area`)**: `tmean` mean `+0.07 °C`, MAE `0.28 °C`, p95 `1.05 °C`, max **`1.84 °C`**; `tmax` max **`3.53 °C`**; `tmin` max **`2.12 °C`**; `humr` MAE `0.73 pp`, p95 `2.90 pp`, max **`8.71 pp`**; `ptot` MAE `2.11 mm`, p95 `9.95 mm`, max **`52.3 mm`** (during Cyclone Yaku).
- **Steep Andean and foothill districts show the largest shifts**:
  - **Ayabaca (`200201`, 27 ERA5-Land cells spanning 10.66 °C to 19.43 °C in March 2023)**: `area = 16.23 °C`, `pop = 16.68 °C` (`+0.45 °C`); `Frias (200202)`: `-0.54 °C`; `Jilili (200203)`: `-0.59 °C`.
  - **Huancabamba (`200301`, 10 ERA5-Land cells spanning 11.62 °C to 16.43 °C)**: `area = 12.70 °C`, `pop = 12.48 °C` (`-0.22 °C`). Note that population weighting does not eliminate the `-5.5` to `-6.4 °C` cold bias relative to the SENAMHI valley-floor station at 1,959 m, because the single 0.1° (~11 km) ERA5-Land cell containing Huancabamba town (50.3% of the district's population) itself averages canyon floor and 3,000+ m ridges (`12.28 °C` in March 2023 vs station `19.49 °C`).
  - **Other steep foothill/Andean districts shift by 0.8 to 1.4 °C**: `Santo Domingo (200409)` `-1.41 °C`, `Salas (140310)` `+1.23 °C`, `Pampas de Hospital (240104)` `+1.13 °C`, `Yamango (200410)` `+1.08 °C`, `Lalaquiz (200305)` `+0.89 °C`, `Huarmaca (200304)` `-0.82 °C`, `Incahuasi (140203)` `-0.82 °C`, `Oyotun (140110)` `+0.78 °C`.
- **Coastal ocean-masked districts (drop-NaN vs nearest-land reassignment)**: When ocean-masked population is dropped and renormalized (`pop`) versus reassigned to the nearest valid land cell (`pop_reassigned`), differences stay small (`0.00` to `0.27 °C`): Santa Rosa (`140114`) shifts `-0.27 °C` (`21.95` to `21.69 °C`, picking the adjacent coastal cell rather than the 0.43% inland sliver), Monsefu (`140108`) shifts `-0.22 °C`, and Eten Puerto (`140104`), Tumbes (`240101`), La Cruz (`240103`), and Zorritos (`240201`) move by `<= 0.02 °C`. Reassigning ocean-masked population to the nearest valid land cell is structurally cleaner for national scale because it guarantees a non-zero weight even when `valid_pop_frac = 0` (e.g., La Punta `070105`).

- **Recommended rule**: **Population-weighted mean using GHS-POP R2023A 3 arc-sec**, with exact pixel-fraction intersection and **nearest-valid-land-cell reassignment** for any ocean-masked populated cell (and nearest-valid-land-cell fallback for uninhabited ocean-masked districts). In dengue forecasting, transmission happens where people live, not on uninhabited Andean peaks or empty Sechura desert; population weighting corrects 0.5 to 1.4 °C elevation distortions in multi-cell Andean and foothill districts.
- **Main alternative**: **Exact area-weighted mean over valid land cells** (with nearest-valid-land-cell fallback when `valid_area = 0`). Simpler (no population raster dependency) and matches CDC Observatorio within `0.16 °C` MAE, at the cost of weighting uninhabited high-altitude terrain equally with valley towns.

## 2. Day boundaries (`America/Lima` vs UTC) and daily extreme definitions

Using 6 complete epi-weeks of 24-hour ERA5-Land (`2023-SE10..SE12` + `2024-SE28..SE30`, 696 district-weeks, area mean, computed 2026-11-25) and 156 complete epi-weeks of 2-hour `total_precipitation` (`2023-2025`, 18,096 district-weeks):

| Variable | Mean diff (`Lima - UTC`) | MAE | p95 abs diff | Max abs diff | Correlation `r` | Sample |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `tmean` (°C) | `-0.009` | `0.026` | `0.063` | `0.096` | `0.99996` | 696 district-weeks (Mar 2023, Jul 2024) |
| `tmax` (mean of daily max, °C) | `+0.000` | `0.000` | `0.000` | `0.000` | `1.00000` | 696 district-weeks |
| `tmin` (mean of daily min, °C) | `-0.008` | `0.008` | `0.058` | `0.173` | `0.99999` | 696 district-weeks |
| `humr` (hourly RH, pp) | `+0.065` | `0.162` | `0.678` | `1.068` | `0.99949` | 696 district-weeks |
| `ptot` (ERA5-Land, mm, 6 wk) | `+0.075` | `0.403` | `2.185` | `4.907` | `0.99991` | 696 district-weeks |
| `ptot` (ERA5-Land, mm, 3 yr) | `-0.002` | `0.779` | n/a | n/a | `0.99750` | 18,096 district-weeks (2023-2025) |

Why the 5-hour offset barely moves weekly values:
- Daily peak temperature in Peru occurs around 13:00 to 16:00 `America/Lima` (18:00 to 21:00 UTC), safely inside the same calendar date in both zones (`MAE = 0.0000 °C`).
- Daily minimum temperature occurs near 05:00 to 06:00 `America/Lima` (10:00 to 11:00 UTC), also inside the same calendar date on almost every day (`MAE = 0.008 °C`).
- Across a 7-day epi-week (168 hours), shifting boundaries by 5 hours alters only 5 of 168 hours (3.0%).

**Weekly extreme definition (`tmax`, `tmin`)**: Comparing against CDC Observatorio (`n = 696`) confirms that `tmax` and `tmin` are **weekly means of the 7 daily maxima / minima** (`bias = -0.03 °C`, `MAE = 0.22 °C` for `tmax`; `bias = +0.03 °C`, `MAE = 0.16 °C` for `tmin`), whereas weekly absolute extremes diverge by `+1.17 °C` (`tmax`) and `-0.78 °C` (`tmin`).

**ERA5-Land precipitation accumulation formula verified**: Because ERA5-Land `total_precipitation` resets at `00:00 UTC` (step 24 at `D+1 00:00` equals the full UTC day `D`), exact `America/Lima` daily precipitation equals `tp(D+1, 00:00) - tp(D, 05:00) + tp(D+1, 05:00)`. Verified against full 24-hour sums across all cells and days in March 2023 and July 2024: maximum discrepancy is **`0.000057 mm`** (float32 rounding).

- **Recommended rule**: Aggregate **ERA5-Land variables on `America/Lima` (UTC-5) Sunday to Saturday epi-week boundaries** (free once hourly ERA5-Land is pulled for RH; costs only +1 day of live latency on Saturday night, i.e., `05:00 UTC` Sunday). Use **weekly mean of 7 daily maxima / minima** for `tmax` and `tmin`. Keep **CHIRPS v3.0 Daily on its native UTC calendar days** (it has no sub-daily product, and our ERA5-Land test shows the 5-hour shift gives `r = 0.9975` and `0.00 mm` bias).
- **Main alternative**: Aggregate **ERA5-Land on UTC calendar days** too. Saves 1 day of live latency (Thursday instead of Friday for 7/7 ERA5-Land days) and keeps ERA5-Land and CHIRPS on the exact same UTC boundary, with `< 0.03 °C` `tmean` and `< 0.2 pp` `humr` difference.

## 3. Relative humidity: hourly versus daily or weekly mean T and Td

Because saturation vapour pressure `e_s(T)` is strongly convex, computing relative humidity from daily-mean or weekly-mean `2m_temperature` and `2m_dewpoint_temperature` systematically underestimates true mean hourly relative humidity (Jensen's inequality).

Across 696 pilot district-weeks (`2023-SE10..SE12` wet summer + `2024-SE28..SE30` dry winter, `America/Lima`, area mean, computed 2026-11-25):

| Comparison | Mean bias (pp) | MAE (pp) | p95 abs diff (pp) | Max abs diff (pp) |
| --- | ---: | ---: | ---: | ---: |
| `RH(daily mean T, Td) - mean(hourly RH)` | **`-1.359`** | `1.359` | `2.685` | **`4.422`** |
| `RH(weekly mean T, Td) - mean(hourly RH)` | **`-1.457`** | `1.457` | `2.732` | **`4.439`** |
| `ECMWF IFS Tetens - Alduchov-Eskridge (Magnus)` | `-0.006` | `0.006` | `0.016` | `0.025` |

The downward bias is larger in dry/clear winter (up to **4.4 pp**) than in cloudy wet summer (`-0.84 pp` mean, max `1.83 pp`) because the diurnal temperature range is wider in winter. Choosing Alduchov-Eskridge (1996) versus ECMWF IFS Tetens saturation vapour pressure over liquid water makes essentially zero difference (`0.006 pp` MAE).

- **Recommended rule**: Compute **hourly relative humidity over liquid water (Alduchov-Eskridge / Magnus, clipped to `[0, 100]`) from hourly `2m_temperature` and `2m_dewpoint_temperature`** before averaging to daily and epi-week means. This also eliminates any need for CDS `derived-era5-land-daily-statistics`.
- **Main alternative**: Derive `humr` from daily mean `T` and `Td`. Avoids hourly retrieval only if daily statistics were fast, which they are not on CDS (2+ hour queue stall), and introduces a seasonally varying `-0.8` to `-4.4 pp` bias.

## 4. Completeness rule for the live, partial epi-week

A MINSA epi-week runs Sunday to Saturday (`America/Lima`). In live operations, ERA5-Land lags 5 to 6 days behind real time and CHIRPS v3.0 `prelim/sat` publishes 2 days after each pentad end (days 2, 7, 12, 17, 22, 27 of each month).

### Partial-week error by `n_dias` (days 1..k of 7 vs full 7-day epi-week)

Measured over **8 years of PISCOp v3.0 pilot daily rainfall** (`2018-2025`, 48,372 complete pilot district-weeks; 6,116 wet epi-weeks `>= 10 mm`) and **8+ years of 10 SENAMHI pilot stations** (`2018-2026`, 3,580 to 3,796 complete station-weeks, computed 2026-11-25):

| `n_dias` | `ptot` raw sum bias (wet `>=10 mm`) | `ptot` raw MAE (wet) | `ptot` scaled `7/n` MAE (wet) | `tmean` MAE (°C) | `tmax` MAE (°C) | `tmin` MAE (°C) | `humr` MAE (pp) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | `-57.0%` | `20.1 mm` | `16.3 mm` | `0.32` | `0.49` | `0.39` | `1.63` |
| 4 | **`-42.6%`** | `14.5 mm` | `12.7 mm` | `0.24` | `0.37` | `0.29` | `1.22` |
| 5 | `-27.8%` | `9.1 mm` | `8.6 mm` | `0.17` | `0.27` | `0.20` | `0.84` |
| 6 | `-13.2%` | `4.2 mm` | `4.6 mm` | `0.09` | `0.15` | `0.11` | `0.46` |

Key lessons:
1. **Never emit an unscaled partial sum as weekly `ptot`**: At `n_dias = 4` (exactly what CDC Observatorio published in `2026-SE45` for all 1,934 national rows), wet rainfall is biased downward by **`-42.6%`**. Linear scaling (`7 / n_dias`) removes the mean bias (`+0.20 mm`) but still leaves large error (`12.7 mm` wet MAE at `n_dias = 4`) because rain falls in isolated storms.
2. **Temperature and RH means are unbiased at every `n_dias`** (`|bias| <= 0.02`), with `tmean` MAE `0.24 °C` at `n_dias = 4` and `0.09 °C` at `n_dias = 6`.

### When full 7-day coverage arrives for the just-ended epi-week

Simulating all 105 complete epi-weeks of 2024 and 2025 (epi-week ending Saturday `S`):
- **ERA5-Land**: reaches Saturday `S` (7/7 UTC days, 6/7 Lima days) on **Thursday `S+5` (~12 UTC)**, and Sunday `S+1 05:00 UTC` (7/7 Lima days) on **Friday `S+6` (~12 UTC)**.
- **CHIRPS v3.0 `prelim/sat`** (pentad end + 2 days):
  - Wednesday `S+4` (Observatorio update day): 7/7 complete in **59.0%** of epi-weeks (`min n_dias = 4`).
  - Thursday `S+5`: 7/7 complete in **77.1%** (`min n_dias = 5`).
  - Friday `S+6`: 7/7 complete in **98.1%** (`min n_dias = 6`).
  - Saturday `S+7`: 7/7 complete in **100.0%** (`min n_dias = 7`).

- **Recommended rule**: **Require `n_dias = 7` for `ptot` (strict completeness gate: never publish partial-week rainfall sums)** and **prefer `n_dias = 7` for all variables** by scheduling the live weekly climate update on **Friday evening `America/Lima` / Saturday morning UTC (`S+6` to `S+7`)**, when both ERA5-Land (`America/Lima`) and CHIRPS v3.0 `prelim/sat` reach 7/7 days (`98.1%` to `100%` of epi-weeks). If an earlier issue-week run (e.g., Wednesday `S+4`) is required, carry an explicit `n_dias` column stamped with `available_at`, emit `tmean/tmax/tmin/humr` only when `n_dias >= 4`, keep `ptot = null` until `n_dias = 7`, and append a new complete (`n_dias = 7`) version when day 7 lands.
- **Main alternative**: Always require `n_dias = 7` for all climate variables and simply treat the just-ended epi-week as missing (`null`) until `S+6`/`S+7` (forecasting on climate lagged through `issue_week - 2` if running on Wednesday). Simplest schema (no partial rows), at the cost of 1 extra week of climate lag for mid-week runs.

## 5. Precipitation comparison: CHIRPS v3.0 vs ERA5-Land vs PISCOp v3.0

We compared **CHIRPS v3.0 Daily (`final/sat`, 0.05°)**, **ERA5-Land (`total_precipitation`, 0.1°)**, and **CDC Observatorio (`ptot`)** against the gauge-calibrated offline benchmark **SENAMHI PISCOp v3.0 (0.1°, GPL 3.0+)** on three complementary scales (all computed 2026-11-25):

1. **Full 3-year weekly series (2023 to 2025, 156 complete epi-weeks, `n = 18,096` pilot district-weeks)**: ERA5-Land vs PISCOp v3.0 vs Observatorio.
2. **Multi-year daily epi-week sample (9 complete epi-weeks spanning 2023-SE10..12 Cyclone Yaku, 2024-SE07..08 wet, 2024-SE28..29 dry, and 2025-SE07..08 wet; `n = 1,044`)**: CHIRPS v3.0 `final/sat` vs ERA5-Land vs PISCOp v3.0 vs Observatorio.
3. **Full 3-year seasonal cycle (36 monthly pentads, days 11 to 15 of every month from January 2023 through December 2025, `n = 4,176`)**: CHIRPS v3.0 `final` vs ERA5-Land vs PISCOp v3.0.

### Pilot-wide summary against PISCOp v3.0

| Product and window | Mean (candidate vs PISCOp) | Bias | MAE | RMSE | Correlation `r` |
| --- | --- | ---: | ---: | ---: | ---: |
| **CHIRPS v3.0 `final/sat`** (9 daily epi-weeks, 2023 to 2025, area) | `27.18` vs `31.71 mm/wk` | `-4.53 mm` | **`16.98 mm`** | **`31.29 mm`** | **`0.781`** |
| **CHIRPS v3.0 `final/sat`** (9 daily epi-weeks, pop-weighted) | `26.36` vs `31.19 mm/wk` | `-4.83 mm` | **`16.62 mm`** | `32.18 mm` | **`0.783`** |
| ERA5-Land Lima (same 9 epi-weeks, area) | `49.64` vs `31.71 mm/wk` | `+17.94 mm` | `27.57 mm` | `45.63 mm` | `0.742` |
| CDC Observatorio `ptot` (same 9 epi-weeks) | `33.46` vs `31.71 mm/wk` | `+1.76 mm` | `18.66 mm` | `32.90 mm` | `0.753` |
| **CHIRPS v3.0 `final`** (36 monthly pentads, Jan 2023 to Dec 2025) | `7.19` vs `6.35 mm/pentad` | **`+0.84 mm`** | **`4.97 mm`** | **`14.22 mm`** | **`0.816`** |
| ERA5-Land Lima (same 36 monthly pentads) | `12.95` vs `6.35 mm/pentad` | `+6.60 mm` | `9.07 mm` | `21.20 mm` | `0.657` |
| ERA5-Land Lima (all 156 epi-weeks, 2023 to 2025) | `19.79` vs `8.29 mm/wk` | **`+11.50 mm`** | `13.91 mm` | `32.28 mm` | `0.680` |
| CDC Observatorio `ptot` (all 156 epi-weeks, 2023 to 2025) | `10.38` vs `8.29 mm/wk` | `+2.09 mm` | `7.44 mm` | `17.86 mm` | `0.705` |

### Breakdown by pilot zone (36 monthly pentads, Jan 2023 to Dec 2025, mm per pentad)

| Zone | CHIRPS v3.0 mean | ERA5-Land mean | PISCOp v3.0 mean | `r(CHIRPS, PISCOp)` | `r(ERA5-Land, PISCOp)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Andean (Ayabaca / Huancabamba) | `16.14` | **`33.86`** | `13.82` | **`0.776`** | `0.569` |
| Lambayeque | `2.92` | **`7.58`** | `3.29` | **`0.847`** | `0.635` |
| Piura (non-Andean) | `6.82` | `9.10` | `6.23` | **`0.840`** | `0.758` |
| Tumbes | `8.56` | **`13.59`** | `5.34` | **`0.815`** | `0.643` |

Independent check against the 10 SENAMHI station rain gauges (`2023 to 2025`, `n = 1,345` complete station-weeks, computed 2026-11-25) confirms the same pattern: station mean is `8.98 mm/wk`, PISCOp v3.0 mean is `7.77 mm/wk` (`MAE = 6.08 mm`, `r = 0.730`), and ERA5-Land mean is `17.91 mm/wk` (`+99%` wet bias, `MAE = 11.20 mm`, `r = 0.736`).

Why CHIRPS v3.0 wins clearly as primary precipitation:
- **Dramatically lower bias and higher correlation everywhere**: Across the full 3-year seasonal cycle, CHIRPS v3.0 hits `r = 0.816` (`MAE = 4.97 mm`) against PISCOp v3.0, beating ERA5-Land (`r = 0.657`, `MAE = 9.07 mm`) in all four pilot zones.
- **ERA5-Land has a massive +100% to +190% wet bias**: Over the full 156 epi-weeks of 2023 to 2025, ERA5-Land averages `19.79 mm/wk` versus PISCOp's `8.29 mm/wk` (`+139%` overall; `48.0` vs `16.5 mm/wk` in Ayabaca and Huancabamba, nearly 3x gauge rainfall).
- **Zero coastal ocean masking on CHIRPS v3.0**: All 116 pilot districts have `valid_area_frac = 1.000` on the 0.05° CHIRPS grid.
- **Population vs area weighting on CHIRPS v3.0**: Closely correlated (`r = 0.986`, `MAE = 2.95 mm/wk`, `bias = -0.82 mm/wk` over the 9 epi-weeks), with population-weighted CHIRPS edging out area-weighted against PISCOp (`r = 0.783` vs `0.781`).

Why ERA5-Land precipitation still has value as an optional companion column:
- It has **near-zero revision** between live `ERA5-Land-T` and final `ERA5-Land` (unlike CHIRPS's 24% median wet-week prelim-to-final revision below).
- Its retrieval cost is negligible if the pipeline already pulls hourly `reanalysis-era5-land` for temperature and humidity (adding `total_precipitation` to the same monthly or weekly request).

- **Recommended rule**: Carry **`ptot_chirps` (CHIRPS v3.0 Daily `prelim/sat` live and `final/sat` history, versioned by `available_at`) as the primary precipitation column**, and **also carry `ptot_era5` (ERA5-Land `total_precipitation`) as a companion column** so modelers can compare or blend a gauge-calibrated, revised signal (`ptot_chirps`) with a near-zero-revision reanalysis signal (`ptot_era5`) at essentially zero extra retrieval cost.
- **Main alternative**: Carry **only `ptot_chirps`** (keeps the panel lean with one canonical column per physical variable, avoiding collinear precipitation features when modelers consume the panel directly).

## 6. CHIRPS v3.0 preliminary-to-final revisions and post-2022 `-9999` gaps

### Preliminary-to-final revision magnitude (`prelim/sat` vs `final/sat`)

Comparing CHIRPS v3.0 `prelim/sat` (available 2 days after each pentad end) against `final/sat` (available ~18 days after month end) over 2026 (`analyze_precip.py`, computed 2026-11-25):

| Test set | Mean `prelim` | Mean `final` | Bias (`final - prelim`) | MAE | p95 abs diff | Max abs diff | Correlation `r` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 daily epi-weeks (`2026-SE07..09` wet + `SE28` dry; `n = 464`) | `25.08 mm` | `26.74 mm` | `+1.66 mm` | `8.17 mm` | `34.49 mm` | `84.95 mm` | `0.922` |
| Wet epi-weeks only (`final >= 10 mm`, `n = 225`) | `48.94 mm` | `53.20 mm` | `+4.26 mm` | **`15.66 mm`** | `45.88 mm` | `84.95 mm` | `0.871` |
| Dry epi-week (`2026-SE28`, `n = 116`) | `0.16 mm` | `0.18 mm` | `+0.02 mm` | `0.03 mm` | `0.05 mm` | `2.24 mm` | `0.999` |
| 30 LatAm pentads across Jan to Oct 2026 (`n = 3,480`) | `4.73 mm` | `5.39 mm` | `+0.66 mm` | `1.94 mm` | `10.83 mm` | `81.90 mm` | `0.909` |
| Wet pentads only (`final >= 10 mm`, `n = 447`) | `30.98 mm` | `35.80 mm` | `+4.82 mm` | `12.41 mm` | `42.97 mm` | `81.90 mm` | `0.833` |

Per-epi-week breakdown in February to March 2026:
- `2026-SE07`: prelim `34.3`, final `35.2 mm` (`bias +0.88`, `MAE 10.10`, `r = 0.950`)
- `2026-SE08`: prelim `46.7`, final `40.6 mm` (`bias -6.07`, `MAE 9.78`, `r = 0.964`)
- `2026-SE09`: prelim `19.2`, final `31.0 mm` (`bias +11.83`, `MAE 12.78`, `p95 = 62.6 mm`, `r = 0.870`)

On wet epi-weeks (`>= 10 mm`), the **median relative revision is `24.1%`** (`31.5%` on wet pentads), with individual district-weeks shifting by up to `46 mm` (p95) to `85 mm` (max). This confirms that **versioning CHIRPS v3.0 in the panel by `available_at`** (storing `prelim/sat` stamped at pentad end + 2 days and appending `final/sat` when published ~18 days after month end) is necessary for honest as-of backtesting. Note also that CHC's `prelim/pentads/latam/tifs/` directory is missing `chirps-v3.0.2025.01.3.tif` (observed 2026-11-25), so historical `prelim/sat` replay before 2025 does not exist on CHC; pre-2025 backtests must use `final/sat` (recording that `prelim` snapshots were not archived before 2025).

### Post-2022 `-9999` infrared gap frequency over Peru

CHC's documentation notes that from 2023 onward, missing geostationary infrared pixels are left as `-9999` rather than gap-filled with ERA5. We audited all downloaded post-2022 CHIRPS v3.0 grids against every land cell inside `DISTRITO.gpkg` (42,468 land cells nationally across 1,890 districts; 1,780 land cells across the 116 pilot districts; computed 2026-11-25):

- **101 daily `final/sat` grids** (`2023-03`, `2024-02`, `2024-07`, `2025-02`, `2026-02..03`, `2026-07` = `4,289,268` Peru land cell-days; `179,780` pilot land cell-days): **`0` days with any `-9999` land pixel (`0.00000%` nationally and in the pilot)**.
- **28 daily `prelim/sat` grids** (`2026-02..03`, `2026-07` = `1,189,104` Peru land cell-days): **`0` days (`0.00000%`)**.
- **66 LatAm pentads covering all 46 post-2022 months** (36 monthly `final` pentads Jan 2023 to Dec 2025 + 30 `prelim` and 30 `final` pentads Jan to Oct 2026): **`0/36`, `0/30`, and `0/30` pentads with any Peru land `-9999` pixel (`0.00000%`)**.

Caveat: because we audited 101 daily grids and 66 pentads rather than all ~1,400 daily grids of 2023 to 2026, whether any isolated `-9999` pixel occurred on an unsampled Amazon day remains `UNCONFIRMED`. Regardless, the operational frequency over Peru is near zero.

- **Recommended rule**: Mask any CHIRPS v3.0 value `< -9000` to `NaN` during aggregation, renormalize spatial weights over valid cells, and set a district-day to `NaN` (failing the `n_dias = 7` completeness gate) if valid weight coverage falls below 50%.
- **Main alternative**: Drop any day with a single `-9999` cell inside a district (stricter, negligible impact given 0% observed incidence).

## 7. Independent temperature check against SENAMHI stations (2018 to 2026)

We discovered that SENAMHI's Observatorio portal (`https://observatorio.senamhi.gob.pe/investigadores/datos`) serves a **public, no-login, no-CAPTCHA JSON API** at `https://servicios.senamhi.gob.pe/api/station/stations/{id}/periods` and `/readings?period=YYYYMM` (verified 2026-11-24). Across Peru, 981 active stations are listed, including 83 meteorological stations in the pilot (46 Piura, 15 Tumbes, 22 Lambayeque).

We downloaded **29,550 daily observations (2018-01 to 2026-11)** for 10 long-running pilot stations spanning main cities, ocean-masked coastal districts, and the Andean stress-test districts Ayabaca and Huancabamba (`fetch_senamhi.py`, `analyze_senamhi.py`). Weekly station `tmean` is `(Tmax + Tmin) / 2` for epi-weeks with `>= 6` station days, compared against district ERA5-Land (`Observatorio` 2018 to 2026, which we verified matches our ERA5-Land area mean to `0.16 °C` MAE):

| Station (code) | District (UBIGEO) | Alt (m) | ERA5-Land area share | Epi-weeks | `r(tmean)` | `r(anomaly)` | `r(week-to-week delta)` | `r(tmax)` | `r(tmin)` | Mean offset (ERA5 - station) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| La Esperanza (`104090`) | Colan (`200504`) | 7 | 78% | 443 | **`0.980`** | `0.952` | `0.707` | `0.949` | `0.982` | `-1.45 °C` |
| Reque (`106046`) | Reque (`140113`) | 13 | 100% (0 centers) | 422 | **`0.969`** | `0.958` | `0.723` | `0.961` | `0.952` | `-0.13 °C` |
| Lambayeque (`106108`) | Lambayeque (`140301`) | 18 | 95% | 438 | **`0.964`** | `0.945` | `0.672` | `0.921` | `0.967` | `+0.18 °C` |
| San Miguel (`105063`) | Catacaos (`200105`) | 24 | 100% | 335 | **`0.964`** | `0.858` | `0.684` | `0.899` | `0.966` | `-2.26 °C` |
| Miraflores (`105100`) | Castilla (`200104`) | 34 | 100% | 254 | **`0.961`** | `0.931` | `0.697` | `0.837` | `0.986` | `-1.58 °C` |
| La Cruz (`100072`) | La Cruz (`240103`) | 6 | 78% (0.3% pop) | 434 | **`0.932`** | `0.918` | `0.547` | `0.647` | `0.952` | `-0.59 °C` |
| El Salto (`103041`) | Zarumilla (`240301`) | 4 | 61% | 281 | **`0.931`** | `0.880` | `0.441` | `0.826` | `0.926` | `-2.09 °C` |
| Ayabaca (`104058`) | Ayabaca (`200201`) | 2,648 | 100% | 444 | **`0.876`** | `0.889` | `0.743` | `0.900` | `0.717` | `+1.27 °C` |
| Puerto Pizarro (`103038`) | Tumbes (`240101`) | 6 | 52% | 339 | **`0.862`** | `0.823` | `0.385` | `0.634` | `0.864` | `-1.36 °C` |
| Huancabamba (`105055`) | Huancabamba (`200301`) | 1,959 | 100% | 443 | **`0.544`** | `0.550` | `0.385` | `0.180` | `0.528` | **`-5.48 °C`** |

What this proves:
1. **Main urban and lowland districts track real temperatures tightly**: `r(tmean) = 0.96` to `0.98`, deseasonalized anomaly `r = 0.86` to `0.96` (`anom_RMSE = 0.45` to `0.66 °C`), and week-to-week delta `r = 0.67` to `0.72`. Even Reque (`140113`, zero ERA5-Land cell centers inside its polygon) hits `r = 0.969` (`r_anom = 0.958`, offset `-0.13 °C`).
2. **Ocean-masked coastal Tumbes districts still track weekly and anomalous changes well**: La Cruz (`240103`, only 0.33% populated area inside valid land cells) hits `r(tmean) = 0.932`, `r(anomaly) = 0.918`, and `r(tmin) = 0.952`. Puerto Pizarro (`240101`, 52% land area; station had all-null 2021) hits `r = 0.862` (`r_anom = 0.823`). Notice that daytime `tmax` is noisier on Tumbes's immediate shoreline (`r_tmax = 0.63` to `0.65`) because of sub-grid sea-breeze cooling, while nighttime `tmin` tracks closely (`0.86` to `0.95`).
3. **Deep Andean canyons are the true resolution limit**: Ayabaca (`2,648 m` ridge town) tracks well (`r = 0.876`, `r_anom = 0.889`, `r_dw = 0.743`, `anom_RMSE = 0.40 °C`), whereas Huancabamba (`1,959 m` valley floor inside a steep canyon) shows both a `-5.48 °C` constant offset and weaker `tmax` tracking (`r_tmax = 0.180`, `r_tmean = 0.544`), because a 0.1° cell mixes canyon floor and 3,200 m slopes. Direct comparison on our 6 hourly epi-weeks (`analyze_senamhi.py`) confirms area mean and population-weighted mean have nearly identical offsets on coastal and canyon stations (within `0.06 °C` on La Cruz and Puerto Pizarro; population-weighting reduces the Piura valley San Miguel offset from `-2.85 °C` to `-2.37 °C`).

## 8. Agreement with CDC Peru Observatorio climate columns

Comparing our hourly ERA5-Land aggregations against CDC Observatorio (`observatorio_20261123T161922Z`, 116 pilot districts, 6 epi-weeks in March 2023 and July 2024, `n = 696`, computed 2026-11-25) explains every single agreement and gap:

1. **Temperature (`tmean`, `tmax`, `tmin`) matches ERA5-Land plain area-weighted UTC mean**:
   - `tmean`: bias `+0.004 °C`, median abs error `0.092 °C`, MAE `0.162 °C`, `r = 0.9973` (369/696 district-weeks within `0.1 °C`).
   - `tmax` (weekly mean of daily max): bias `-0.033 °C`, MAE `0.217 °C`.
   - `tmin` (weekly mean of daily min): bias `+0.032 °C`, MAE `0.161 °C`.
   - Population weighting moves MAE vs Observatorio from `0.162 °C` to `0.372 °C` because Observatorio uses area means, not population weights.
   - The largest residual differences (`0.5` to `1.1 °C` in 10 steep Andean districts like San Miguel de El Faique and Yamango) reflect boundary/grid-alignment differences in steep terrain.
2. **Relative humidity (`humr`) gap (`+1.44 pp`) is fully explained**:
   - Our hourly RH sits `+1.44 pp` above Observatorio (`MAE = 1.44 pp`), whereas RH computed from daily-mean `T` and `Td` matches Observatorio closely (`bias = +0.08 pp`, median abs error `0.28 pp`, `MAE = 0.38 pp`). Observatorio clearly computes `humr` from daily mean `T` and `Td` rather than hourly values, underestimating RH by `~1.4 pp` (up to `4.4 pp` in winter).
   - Observatorio also has a national 4-epi-week `humr` outage (`2025-SE19` to `2025-SE22`, 464 missing pilot rows).
3. **2026 coastal ocean-mask bug in Observatorio**:
   - Starting `2026-SE01`, 13 small coastal districts nationally (including `140104` Eten Puerto in the pilot) turned all-`NaN` for `tmean`, `tmax`, `tmin`, and `humr` while keeping `ptot` populated. In 2023-2024 our Eten Puerto `area` mean (`21.686 °C`) matched Observatorio (`21.683 °C`) to `0.003 °C`.
4. **Precipitation (`ptot`) source mismatch**:
   - Across 2023 to 2025 (18,096 pilot district-weeks), Observatorio `ptot` averages `10.38 mm/wk` (Andean `16.9 mm/wk`), far below ERA5-Land (`19.79 mm/wk`, Andean `48.0 mm/wk`) and much closer to PISCOp v3.0 (`8.29 mm/wk`, Andean `16.5 mm/wk`; `r = 0.705`). Together with Eten Puerto keeping `ptot` in 2026 when ERA5-Land went null, this shows Observatorio's `ptot` comes from a satellite-based grid (consistent with its `Informacion` tab citing NASA GPM IMERG, contradicting its chart footers that cite ERA5-Land), even though Observatorio applies ERA5-Land's `n_dias = 4` truncation to `ptot` in `2026-SE45`.

## 9. Operational notes and disk usage

### Upstream API and rate-limit observations (2026-11-24 and 2026-11-25)

1. **Copernicus CDS (`reanalysis-era5-land` vs `derived-era5-land-daily-statistics`)**:
   - All requests ran strictly sequentially (one at a time) with `"download_format": "unarchived"`, producing zero `403` or `429` errors.
   - `derived-era5-land-daily-statistics` remained in `accepted` for over 2 hours for a single day of one variable (cancelled cleanly via `remote.delete()`), omits `total_precipitation`, and cannot produce hourly RH.
   - `reanalysis-era5-land` completed reliably: 1 month of 24-hour 3-variable pilot NetCDF (`43 x 28` grid) took 13 to 28 minutes (`3.8` to `4.5 MB`); 1 full year of 2-hour `total_precipitation` (`00:00` and `05:00` UTC) took 3 to 11 minutes (`1.6` to `1.8 MB`).
   - Because CDS requests occasionally drop the polling TCP connection (`RemoteDisconnected` / `Read timed out`), production code should use `cdsapi>=0.7.7` retry handling and never run parallel CDS jobs.
2. **Climate Hazards Center (`data.chc.ucsb.edu`)**:
   - CHC's nginx server rejects GDAL `/vsicurl/` COG burst reads immediately with `429 Too Many Requests` and stalls on multi-gigabyte `byYear` (`3.2 GiB`) and `byMonth` (`250 MB`) global NetCDFs.
   - Single-connection sequential downloads of per-day GeoTIFFs (`11` to `12 MB`) and LatAm pentad GeoTIFFs (`3.3 MB`) succeed cleanly when spaced `>= 3` to `5` seconds apart with exponential backoff on `429`. For the production backfill (`2000 to 2026`), consider also checking WFP's public CHIRPS v3.0 COG mirror or GEE (`UCSB-CHC/CHIRPS/V3/DAILY_SAT`) during stack planning (#20) if CHC throttling slows bulk backfill.
3. **SENAMHI Observatorio public API**:
   - `https://servicios.senamhi.gob.pe/api/station/stations/actives`, `/periods`, and `/readings?period=YYYYMM` worked with no CAPTCHA and no login (981 active stations nationally; 83 meteorological stations in the pilot; 29,550 daily rows downloaded cleanly in ~5 minutes).
4. **License hygiene**:
   - SENAMHI `PISCOp_d.nc` (`GPL 3.0+`) was kept strictly inside gitignored prototype storage as an offline benchmark only and never enters git or panel outputs.

### Total disk used (gitignored prototype storage)

Total under `/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week/`: **`1.6 GB`** (measured 2026-11-25):

| Path | Size | Contents |
| --- | ---: | --- |
| `PISCOp_d.nc` + `PISCOp_readme.txt` | `1.5 GB` | SENAMHI PISCOp v3.0 daily NetCDF benchmark (1981 to 2025, GPL 3.0+) |
| `ghspop/` | `90 MB` | GHS-POP R2023A 3 arc-sec tiles (`E2020` and `E2000`, `R10_C10` + `R10_C11`) + pilot mosaics + docs |
| `chirps_v3_peru/` | `45 MB` | Peru-clipped CHIRPS v3.0 daily (`final/sat` and `prelim/sat`) and 66 LatAm pentad NetCDFs |
| `era5land/` + test file | `14.3 MB` | Pilot hourly `2023-03` and `2024-07`, 2-hour `tp` for `2023`, `2024`, `2025`, and 2-day test |
| `senamhi/` + `senamhi_actives.json` | `1.1 MB` | Active station catalog (981 stations) and 10 pilot stations daily parquet (`2018 to 2026`) |
| Derived parquet tables and `weights/` | `8.2 MB` | Spatial weights, MINSA calendar, Observatorio pilot cache, PISCOp/ERA5 weekly caches, summaries |

## 10. Decisions needed from the user

1. **Spatial aggregation**: Confirm **GHS-POP R2023A 3 arc-sec population-weighted mean (with nearest-valid-land-cell reassignment for ocean-masked coastal population)** as the panel default, or prefer **exact area-weighted mean** (simpler, matches Observatorio within `0.16 °C` MAE, no population raster dependency)? If population-weighted, confirm whether to freeze one static epoch (e.g., `E2020`, since `E2020` vs `E2000` differs by only `0.010 °C` MAE) or step across 5-year epochs (`E2000` to `E2025`) gated by `available_at`.
2. **Day boundary for ERA5-Land**: Confirm **`America/Lima` (UTC-5)** for ERA5-Land (matches MINSA epi-weeks exactly; reaches 7/7 days on Friday `S+6`) while keeping CHIRPS v3.0 on native UTC calendar days, or use **UTC** for both (ERA5-Land reaches 7/7 days on Thursday `S+5`, with `< 0.03 °C` `tmean` and `< 0.2 pp` `humr` difference)?
3. **Relative humidity**: Confirm **hourly RH over liquid water (Alduchov-Eskridge / Magnus)** computed from hourly ERA5-Land `2m_temperature` and `2m_dewpoint_temperature` before daily and epi-week averaging (avoids the `-1.4 pp` daily-mean bias and avoids CDS `derived-era5-land-daily-statistics` queue stalls)?
4. **Live partial epi-week completeness**: Confirm **strict `n_dias = 7` for `ptot`** (never emit unscaled partial sums, which bias wet rainfall `-42.6%` at `n_dias = 4`) and choose between: (a) running the weekly live climate update on **Friday evening `America/Lima` / Saturday morning UTC (`S+6` to `S+7`)** so all variables arrive complete (`n_dias = 7`), or (b) emitting versioned partial temperature/RH rows (`n_dias >= 4`, with `n_dias` stored) on Wednesday while keeping `ptot = null` until `n_dias = 7`?
5. **Precipitation column(s) in the panel**: Confirm carrying **`ptot_chirps` (CHIRPS v3.0 Daily `prelim/sat` live and `final/sat` history, versioned by `available_at`) as the primary precipitation column**, plus **`ptot_era5` (ERA5-Land `total_precipitation`) as an optional near-zero-revision companion column**, or prefer carrying **`ptot_chirps` only** to keep one canonical column per variable?
