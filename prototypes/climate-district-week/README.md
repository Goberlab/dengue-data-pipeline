# Climate district epi-week aggregation prototype (ticket #24)

Throwaway prototype scripts that test how gridded climate sources (ERA5-Land, CHIRPS v3.0, and benchmark SENAMHI PISCOp v3.0) turn into district (6-digit UBIGEO) by epi-week values over the Peru pilot (Piura, Tumbes, Lambayeque).

All downloaded rasters, NetCDFs, and derived parquet tables live outside git under:

`/Users/rodrigocastillo/.t3/projects/dengue-data-pipeline/data/prototypes/climate-district-week/`

Findings and recommendations live in [`docs/prototypes/climate-district-week.md`](../../docs/prototypes/climate-district-week.md).

## Scripts (PEP 723, run with `uv run`)

1. `prepare_observatorio.py`: builds the MINSA epi-week calendar and caches pilot CDC Observatorio climate rows (`2018-SE01` to `2026-SE45`).
2. `spatial_weights.py`: builds exact area-weighted, GHS-POP R2023A 3 arc-sec population-weighted, and cell-center weights for the 116 pilot districts on ERA5-Land and PISCOp v3.0 grids.
3. `fetch_era5land.py`: sequential CDS API fetcher (one request at a time, `download_format="unarchived"`) for hourly pilot windows (`2023-03`, `2024-07`) and 2-hour daily precipitation (`2023`, `2024`, `2025`).
4. `fetch_senamhi.py`: fetches 2018-2026 daily station readings for 10 representative pilot stations from SENAMHI's public Observatorio JSON API (`servicios.senamhi.gob.pe/api/station/stations/...`).
5. `fetch_chirps.py`: politely fetches CHIRPS v3.0 daily `final/sat`, daily `prelim/sat`, and LatAm pentad GeoTIFFs from `data.chc.ucsb.edu`, clipping each immediately to Peru.
6. `analyze_hourly.py`: compares `America/Lima` vs UTC day boundaries, hourly RH vs daily/weekly-mean T/Td RH, spatial weighting schemes (including Ayabaca, Huancabamba, and ocean-masked coastal districts), and CDC Observatorio agreement.
7. `analyze_senamhi.py`: compares weekly district temperature series against 10 SENAMHI stations (2018-2026).
8. `analyze_completeness.py`: quantifies partial epi-week errors (`n_dias = 1..6` vs `7`) and live source arrival timing.
9. `analyze_precip.py`: compares CHIRPS v3.0 (`final/sat` and `prelim/sat`), ERA5-Land precipitation, PISCOp v3.0, and Observatorio, and audits post-2022 CHIRPS v3.0 `-9999` IR gaps across Peru.
