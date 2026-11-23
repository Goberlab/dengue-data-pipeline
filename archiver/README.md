# Archiver

CDC Perú replaces its dengue dashboards in place, and the national case file on datosabiertos is overwritten about once a year. Nobody else keeps the old copies, so each day not captured is lost. The archiver keeps a dated **snapshot** of each source, so later work can replay what was known on each date (see `available_at` in `GLOSSARY.md`).

It runs once a day on GitHub Actions in the private [Goberlab/dengue-data-archive](https://github.com/Goberlab/dengue-data-archive) repo (its `.github/workflows/archive.yml`, 23:17 UTC = 18:17 Lima), one job per source. That workflow checks out this repo's `main` and runs `archiver/archive.py`. It can also be started by hand from that repo's Actions tab, for one source, a subset of departments, or another ref of this repo.

## Sources

| Source | What is saved | When a snapshot is taken | Checks that fail the run |
|---|---|---|---|
| `sala-diaria`: [Sala situacional diaria de dengue](https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html) | The raw HTML (gzipped) and its four embedded workbooks (department indicators, district indicators, district cases by clinical form, death records) | When the page's ETag or Last-Modified changes. One conditional request a day. | Truncated or short body, no closing `</html>`, fewer than 30 widget payloads, no "Fecha de corte", the four workbooks missing or not valid xlsx |
| `observatorio`: [Observatorio de Clima y Salud](https://app7.dge.gob.pe/maps2/shiny_observatorio_web/) | The "Descargar base" workbook per department and case class (confirmed, probable), 2018 to the current year: district × epi-week cases plus the app's weekly climate columns | When the page's "Semana de corte" changes, or 7 days after the last capture | Inputs that will not hold, non-xlsx response, missing `Distrito` sheet, bad UBIGEO, wrong department or case class in rows, districts with unequal week counts, years not matching the request |
| `datosabiertos`: [Vigilancia epidemiológica de dengue](https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue) | The `package_show` metadata JSON, and each listed CSV (gzipped) | Metadata when its hash changes. A CSV when its Content-Length or Last-Modified changes and its hash differs. | API not `success`, truncated CSV, header without `ubigeo`, `ano` and `semana`, fewer than 100,000 lines |
| `sala-pdf`: Sala situacional dengue PDF (`dge.gob.pe/portal/docs/vigilancia/sala/<year>/SE<nn>/dengue.pdf`) | Each weekly PDF | Weeks in the last six not yet held, or whose Last-Modified moved | Not a PDF, truncated |

A run that finds nothing new uploads nothing and only updates its bookkeeping. A failed check exits non-zero, which turns the Actions run red and emails whoever last edited the schedule.

### Source quirks worth knowing

- **datosabiertos** answers HTTP 418 to any User-Agent that isn't a plain browser string, including one that names this project. CDC Perú's servers accept a named client, so they get one.
- **Observatorio** is an R Shiny app. Its export exists only inside a live session, so the job drives headless Chromium: it sets the inputs, presses "Click para mostrar / Procesar", then fetches the download URL. The year slider defaults to the last two years and limits the export, so the job widens it to the slider's full range. Epi-weeks after the cut are padded with `Casos = 0` and an empty `Tipo caso`. Those zeros are not data. The `Pais` (national) export double-counts Lima Metropolitana and is not captured.

## Where snapshots live

Snapshots are GitHub release assets of the private [Goberlab/dengue-data-archive](https://github.com/Goberlab/dengue-data-archive) repo, outside every branch's git history. It is private because the dashboard snapshots include MINSA's individual death records and most sources carry no explicit license (only the datosabiertos file is ODC-BY). It can be made public later; a public upload can't be taken back.

- One release per source per month, tagged `<source>-YYYY-MM` (UTC month of the fetch).
- Each snapshot is a set of assets sharing one timestamp, `<source>_<YYYYMMDDTHHMMSSZ>_<file>`, plus `<source>_<timestamp>_meta.json`. The metadata file records fetch time in UTC and Lima time, the URL, HTTP validators, byte counts and SHA-256 of the uncompressed payload, what the checks saw (cut date or week, districts, rows), and the archiver commit and run.
- The `archive-state` release holds one `state-<source>.json` per source: the last fingerprint seen. It's bookkeeping, not data.

List and fetch:

```sh
R=Goberlab/dengue-data-archive
gh release list -R $R
gh release view observatorio-2026-11 -R $R --json assets --jq '.assets[].name'
gh release download observatorio-2026-11 -R $R -p '*20261123T161922Z*' -D snapshots/
```

## Running it by hand

```sh
uv run archiver/archive.py sala-diaria                     # stage only, into data/archive-staging/
uv run archiver/archive.py observatorio --departments PIURA,TUMBES --force
uv run archiver/archive.py datosabiertos --publish OWNER/REPO   # stage and upload
```

The first Observatorio run needs `uvx playwright@1.64.1 install chromium-headless-shell`. Staging-only runs keep their state in `data/archive-staging/state-<source>.json`, separate from the published state.

## If GitHub's runners get blocked

On 2026-11-23, runners (US Azure IPs) reached all four sources, provided datosabiertos got a plain browser User-Agent. If that changes, run the same commands with `--publish` from a machine on a Peruvian IP, for example a macOS launchd job that runs `uv run archiver/archive.py <source> --publish <repo>` daily, with `gh` logged in.

## Known risks

- The schedule spends the archive repo's private Actions minutes (the free organization plan includes 2,000 a month). Expect roughly 200 a month: four short jobs a day plus a weekly Observatorio capture of about 15 minutes.
- CDC Perú can change page layouts without notice. The checks are there to make that a red run instead of a silent gap.
