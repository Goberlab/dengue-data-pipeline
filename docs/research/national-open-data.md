# National open-data and bulletin sources for dengue in Peru

## Short answer

Only one national open-data source publishes a complete district by epi-week dengue series: the CDC Perú case file on Datos Abiertos (`datos_abiertos_vigilancia_dengue_2000_2025_0.csv`), which covers 2000 through 2025 by onset week, place of infection (6-digit INEI UBIGEO), and case class (confirmed and probable) under ODC-BY, but updates roughly once per year after annual closure and contains zero 2026 rows. CDC Perú's weekly Boletín Epidemiológico (PDF only, 1993 to 2026 SE 37, about 9 to 10 epi-weeks behind) reports dengue only by department or regional health directorate, not by district. CDC Perú's weekly Sala Situacional de Dengue PDFs (2020 to 2026 SE 44) include a per-department table of only the top 9 or 10 districts for cumulative year-to-date cases and the single latest epi-week, lumping 23% to 26% of pilot-region cases into `DEMAS DISTRITOS`. REUNIS holds no native dengue surveillance series (its Metaxénicas page links to a stale 2026 SE 25 CDC PDF) and its own HIS-MINSA and SEEM clinical dashboards are annual or monthly healthcare encounter counts. No national public source records which individual notifying units or districts reported or filed negative notification each epi-week, so absent district-epi-weeks cannot be coded as verified zeros from public data.

## Source profiles

All URLs and HTTP responses below were verified on 2026-11-22 (2026-11-23 UTC).

### Datos Abiertos national dengue case file (CDC Perú / MINSA)

Source page: [Vigilancia Epidemiológica de dengue](https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue) (package UUID `2c3b2955-6252-4b9d-abd3-caeb61ccda39`, resource UUID `79e21c8d-3a94-4ac5-b234-bace71fe9675`).

| Attribute | Value |
|---|---|
| Geography | National, down to district (6-digit INEI UBIGEO; 662 distinct 6-digit codes and zero empty UBIGEO values in the live 1,065,274-row file) plus optional `localidad` and `localcod` ([package_show](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue); [live CSV](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2025_0.csv)). |
| Time basis | Onset week (`ano`, `semana` 1 to 53; epi-week 53 appears in 2003, 2008, 2009, 2014, 2020, and 2025). No notification week or publication date column exists in the CSV ([package_show](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue)). |
| Place basis | Place of infection for `distrito`, `ubigeo`, and `localcod`; notifying regional directorate for `diresa` ([package_show](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue)). |
| Case classes | Confirmed (`C`, 955,112 rows) and probable (`P`, 110,162 rows) only in the live file; zero suspected (`S`) and zero discarded rows, even though the data dictionary lists `S = Sospechoso`. Clinical severity is also present via `diagnostic` (`A97.0`, `A97.1`, `A97.2`) and `enfermedad` ([live CSV](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2025_0.csv)). |
| Coverage | 2000 epi-week 1 through 2025 epi-week 53 (26 full years, 1,065,274 individual case rows). Zero 2026 rows ([live CSV](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2025_0.csv)). |
| Cadence | Observed cadence is roughly annual after full-year closure: launched 2023-11-22 (2000 to 2022), then updated 2024-12-11 (through 2023), 2025-12-16/17 (through 2024), and 2026-10-21/22 (through 2025) ([package_revision_list](https://www.datosabiertos.gob.pe/api/3/action/package_revision_list?id=vigilancia-epidemiol%C3%B3gica-de-dengue); [CDC launch note](https://www.dge.gob.pe/portalnuevo/informacion-publica/prensa/cdc-peru-presento-plataforma-de-datos-abiertos-2/)). The description text claims weekly or monthly updates, copied from the Boletín Epidemiológico colophon, which contradicts actual uploads. |
| Access method | Direct CSV download (`117,866,478` bytes) and DKAN/CKAN-compatible JSON metadata API on Drupal 7 (`package_show`, `package_list`, `package_revision_list`, `resource_show`, and DCAT RDF/XML at [`.xml`](https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue.xml)). Requires a standard browser `User-Agent` header; default `curl` receives HTTP 418 from CloudWAF. |
| License | Open Data Commons Attribution License (ODC-BY), `http://opendefinition.org/licenses/odc-by/` ([package_show](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue)). |

DKAN API quirks verified directly:
- `https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue` returns HTTP 200 JSON; the unaccented slug `vigilancia-epidemiologica-de-dengue` returns HTTP 404.
- `https://www.datosabiertos.gob.pe/api/3/action/package_list` returns HTTP 200 with 3,677 package slugs.
- `https://www.datosabiertos.gob.pe/api/3/action/package_revision_list?id=vigilancia-epidemiol%C3%B3gica-de-dengue` returns HTTP 200 JSON with all 6 package revisions and UTC revision times; `resource_show?id=79e21c8d-3a94-4ac5-b234-bace71fe9675` returns HTTP 200 JSON.
- `https://www.datosabiertos.gob.pe/api/3/action/package_search?q=dengue` fails for API use, returning HTTP 301 to the HTML page `https://www.datosabiertos.gob.pe/dengue`.
- `https://www.datosabiertos.gob.pe/api/3/action/datastore_search?resource_id=79e21c8d-3a94-4ac5-b234-bace71fe9675&limit=2` returns HTTP 302 to `/api/action/datastore/search.json?...`, which returns HTTP 500 (`Resource 79e21c8d-3a94-4ac5-b234-bace71fe9675 does not exist`), so row-level API queries are unavailable.
- Sibling CDC Perú surveillance packages (`vigilancia-epidemiológica-de-enfermedad-diarreica-aguda-eda`, `vigilancia-epidemiologica-de-infecciones-respiratorias-agudas-ira`, `vigilancia-epidemiológica-de-enfermedad-de-carrión`, `vigilancia-epidemiológica-de-leishmaniosis`, `vigilancia-epidemiológica-de-malaria`, `vigilancia-epidemiológica-de-las-zoonosis`) share the same annual release pattern (all modified 2026-10-21 or 2026-10-23; [CDC tag search](https://www.datosabiertos.gob.pe/search/field_tags/cdc-peru-1539)).

### CDC Perú weekly Boletín Epidemiológico del Perú

Index page: [Boletines epidemiológicos](https://www.dge.gob.pe/portalnuevo/informacion-publica/boletines-epidemiologicos/) (note: `https://www.dge.gob.pe/portalnuevo/boletines-epidemiologicos/` returns HTTP 404). The page embeds two iframes hosted on [Epi-Publicaciones](https://epipublic.dge.gob.pe/publico/listado/1/2026/0) and [search](https://epipublic.dge.gob.pe/publico/buscar/), populated via `POST https://epipublic.dge.gob.pe/publico/listado_ajax` (`bq_categoria=1`).

| Attribute | Value |
|---|---|
| Geography | National (`Tabla 1`) and department / regional health directorate (`Tabla 2 - A`, 29 GERESA/DIRESA/DISA/DIRIS in 2026 SE 37; 32 in 2015 SE 52 and 2025 SE 53). No district by epi-week dengue table exists in any inspected issue (2005 SE 52, 2015 SE 52, 2025 SE 53, 2026 SE 37). Only the ad-hoc `Brotes y otros EVISAP` table names individual districts where new outbreaks were logged in SIEpi-Brotes ([2026 SE 37 PDF](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202637_20_145551.pdf); [2025 SE 53 PDF](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202553_19_162849.pdf); [2015 SE 52 PDF](https://www.dge.gob.pe/portal/docs/vigilancia/boletines/2015/52.pdf); [2005 SE 52 PDF](https://www.dge.gob.pe/boletines/2005/52.pdf)). |
| Time basis | Single issue epi-week plus cumulative year-to-date totals in `Tabla 1` (national); cumulative year-to-date totals only in `Tabla 2 - A` (regional). Whether counts are dated by onset week or notification week is UNCONFIRMED from the PDF tables themselves (neither term appears in `Tabla 1` or `Tabla 2 - A` in 2026 SE 37 or 2025 SE 53). |
| Place basis | UNCONFIRMED in the Boletín tables themselves (`Tabla 2 - A` groups by `Departamento` and `Direcciones de salud` without stating whether counts follow place of infection or notifying directorate). |
| Case classes | In 2025 SE 53 and 2026 SE 37, `Tabla 1` splits national dengue counts by clinical form (`Dengue sin signos de alarma`, `Dengue con signos de alarma`, `Dengue grave`) and by `Confirmados` vs `Probables`; `Tabla 2 - A` combines confirmed and probable cases by clinical form and total dengue. In 2015 SE 52, `Tabla 1` and `Tabla 2 - A` do not split confirmed vs probable. In 2005 SE 52 (`Indicadores semanales de dengue`), cases are split into `Dengue clásico` and `Dengue hemorrágico` with `C`, `P`, and `D` (discarded) columns by DISA ([2005 SE 52 PDF](https://www.dge.gob.pe/boletines/2005/52.pdf)). |
| Coverage | Archive lists 34 years, 1993 through 2026 (verified HTTP 200 on [1993 SE 52](https://epipublic.dge.gob.pe/uploads/boletin/boletin_199352.pdf), 2005 SE 52, 2015 SE 52, [2020 SE 53](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202053.pdf), 2025 SE 53, and 2026 SE 37). Some years have fewer than 52 issues (for example, 2020 lists 25 PDFs in `epipublic`). |
| Cadence | Nominally weekly (`52 o 53 números` per year), but published with a substantial lag: as of 2026-11-22 (2026 epi-week 47), the newest issue is 2026 SE 37 (published `20-11-2026`, `Last-Modified: Fri, 20 Nov 2026 19:55:51 GMT`, a lag of roughly 9 to 10 epi-weeks; [detalle 5593](https://epipublic.dge.gob.pe/publico/detalle/5593)). |
| Access method | PDF only (zero XLSX, CSV, or ZIP files in `bq_categoria=1` across all tested years 1993 to 2026). Programmatic discovery via `POST https://epipublic.dge.gob.pe/publico/listado_ajax` (`bq_anio=<year>&bq_categoria=1`). |
| License | No open-data license stated on the portal or inside the PDF colophon (provisional data disclaimer only; [2026 SE 37 PDF](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202637_20_145551.pdf), p. 22). |

### CDC Perú weekly Sala Situacional de Dengue PDFs and Sala Situacional archive

Index page: [Sala de situación](https://www.dge.gob.pe/portalnuevo/sala-de-situacion/) and Epi-Publicaciones (`bq_categoria=6` for general Sala Situacional, 2005 to 2024; `bq_categoria=13` for `dengue-semanal`, 2020 to 2024 SE 19, e.g., [2024 SE 19](https://epipublic.dge.gob.pe/uploads/dengue-semanal/dengue-semanal_202419_20_110941.pdf)). The active weekly archive sits under `https://www.dge.gob.pe/portal/docs/vigilancia/sala/<YEAR>/<SE>/dengue.pdf` (plus combined national `salaSE<WW>.pdf` and `salaSE<WW>.zip`).

| Attribute | Value |
|---|---|
| Geography | National, department (full weekly table on p. 5 of [2026 SE 44 dengue.pdf](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/SE44/dengue.pdf) collapses epi-weeks 1 to 27 into one column and lists epi-weeks 28 to 44 individually), and **truncated district tables** per department: only the top 9 districts (in 2026 SE 44; top 10 in [2020 SE 53 dengue.pdf](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2020/SE53/dengue.pdf)) plus a lumped `DEMAS DISTRITOS` row, using district names with no UBIGEO codes. In 2026 SE 44, `DEMAS DISTRITOS` hides 4,058 of 17,459 YTD cases in Piura (23.24%, p. 23), 4,161 of 15,793 in Lambayeque (26.3%, p. 53), and 72 of 2,683 in Tumbes (2.68%, p. 62). National district maps (p. 11 and p. 12) are static choropleths without tables. |
| Time basis | Per-department district tables give cumulative YTD totals for the current and prior year plus the single current epi-week (`Casos en la SE 44 2026`). No district by epi-week matrix exists in the PDF. Whether case counts are dated by onset week or notification week is UNCONFIRMED from the PDF text (`inicio de síntomas` does not appear in the 109-page 2026 SE 44 deck). |
| Place basis | The 2026 SE 44 dengue death table (p. 20) labels the regional breakdown as `Lugar probable de infección`; the case tables do not state their place basis explicitly (UNCONFIRMED from the PDF alone). |
| Case classes | Confirmed and probable cases combined in the district tables and department weekly matrix; confirmed vs probable splits appear only at the department YTD level (p. 8) and in unlabeled stacked bar charts (p. 9 and department slides). Deaths are split into `Relacionadas a Dengue` and `En Investigación` (p. 20). |
| Coverage | Standalone `dengue.pdf` exists from **2020 SE 01 through 2026 SE 44** (verified HTTP 200 for [2020 SE 01](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2020/SE01/dengue.pdf), [2020 SE 53](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2020/SE53/dengue.pdf), [2024 SE 52](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2024/SE52/dengue.pdf), [2025 SE 53](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2025/SE53/dengue.pdf), and [2026 SE 44](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/SE44/dengue.pdf); 2019 and earlier plus 2026 SE 45 to SE 48 return HTTP 302 to `https://www.dge.gob.pe/portalnuevo/`). Combined national `salaSE<WW>.pdf` runs from **2015 SE 01 through 2026 SE 44** (2014 returns HTTP 302), and `salaSE<WW>.zip` runs from **2005 through 2026** (verified HTTP 200 on [2005 SE 52 zip](https://www.dge.gob.pe/vigilancia/sala/2005/salaSE52.zip), [2008 SE 52 zip](https://www.dge.gob.pe/vigilancia/sala/2008/salaSE52.zip), [2009 SE 52 zip](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2009/salaSE52.zip) through [2026 SE 44 zip](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/salaSE44.zip); 2004 returns HTTP 302). The 2005 `salaSE52.pdf` has only national and DISA-level dengue endemic channels, no district tables. |
| Cadence | Weekly, roughly 2 to 3 epi-weeks behind the current date: 2026 SE 44 `dengue.pdf` has `Last-Modified: Wed, 18 Nov 2026 13:42:25 GMT` and PDF `CreationDate: 2026-11-18 08:42 -05` (published during 2026 epi-week 47). |
| Access method | Static PDFs (exported via `Microsoft: Print To PDF` from PowerPoint with heavy diagonal `MINSA / CDC` watermarks) and ZIP archives containing PDFs only (`2026/salaSE44.zip` contains 24 disease PDFs, zero XLSX or CSV files). Probing `2026/SE44/dengue.xlsx` returns HTTP 302 to `/portalnuevo/`; directory indexes return HTTP 403. |
| License | No open-data license stated on `dge.gob.pe` or inside the PDFs. |

Note on interactive CDC Perú dashboards: `https://www.dge.gob.pe/portalnuevo/sala-de-situacion/` also links to interactive dashboards including `https://www.dge.gob.pe/sala-situacional-dengue/` (HTTP 302 to `https://app7.dge.gob.pe/maps/sala_metaxenica/`), `https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html`, `https://app7.dge.gob.pe/maps2/shiny_dengue_heatmap_web/`, `https://app7.dge.gob.pe/maps2/shiny_metaxenicas_web/`, `https://app7.dge.gob.pe/maps2/shiny_febriles_web/`, and `https://www.dge.gob.pe/sala-brotes/`. Their underlying feeds are covered in issue #3 rather than duplicated here.

### REUNIS (MINSA)

Portal: [REUNIS](https://www.minsa.gob.pe/reunis/) (returns HTTP 403 to a minimal `Mozilla/5.0` User-Agent; returns HTTP 200 with full browser `User-Agent` and `Accept` headers).

REUNIS hosts **no native dengue surveillance series**. Its `Enfermedades Metaxénicas` menu (`?op=2&niv=4`) links directly out to CDC Perú's PDFs and was stale at [2026 SE 25 dengue.pdf](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/SE25/dengue.pdf) on 2026-11-22 while CDC Perú had already published SE 44. Its `Epidemiología` menu (`?op=2&niv=7`) likewise only links out to CDC Perú's Boletines, Sala Situacional, and `sala-situacional-dengue`. Its dengue vaccination view (`?op=2&niv=9&tbl=6`, Tableau workbook [VacunacionDengue](https://public.tableau.com/profile/api/single_workbook/VacunacionDengue), updated 2026-11-20) tracks daily district-level vaccine doses (ages 10 to 20), not dengue cases.

REUNIS does host three Tableau Public clinical/administrative workbooks where ICD-10 (`CIE-10`) codes can appear, none of which are surveillance case series:

#### REUNIS Morbilidad General (HIS-MINSA)

Page: [Morbilidad General](https://www.minsa.gob.pe/reunis/index.asp?op=3&niv=6&tbl=1); Tableau workbook [MorbilidadHIS_17623572690380](https://public.tableau.com/profile/api/single_workbook/MorbilidadHIS_17623572690380) (prior years at [Morbilidad_HIS_2024](https://public.tableau.com/profile/api/single_workbook/Morbilidad_HIS_2024)); Excel archive button inside the workbook points to [Versión HISMINSA.zip](https://cloud.minsa.gob.pe/s/rDP3GeGsziwYjgx/download).

| Attribute | Value |
|---|---|
| Geography | National, department, province, and district (`Departamento`, `Provincia`, `Distrito`, `ubi eess (DISTRITO)` in `Morbilidad HIS.twb`). |
| Time basis | Annual in the published Tableau view (`yr:fec_aten:ok`, consultation date `fec_aten` aggregated by calendar year; no epi-week or month axis in the view). |
| Place basis | Health facility district (`ubi eess (DISTRITO)` in the workbook schema), not place of infection. |
| Case classes | Clinical outpatient encounters in HIS-MINSA coded by 3-character ICD-10 category (`cod_cat`, including `A97` references in the workbook XML), not surveillance confirmed or probable cases; excludes EsSalud and private facilities not reporting to HIS-MINSA. |
| Coverage | Live workbook displays 2026 (updated `2026-11-06`, title stamp `02 Noviembre 2026`); prior-years workbook (`Morbilidad_HIS_2024`, updated `2026-02-02`) and `Versión HISMINSA.zip` (confirmed to contain annual pivot workbooks such as `MORBILIDAD 2019 HISMINSA.xlsx`; full year span inside the archive > 25 MB is UNCONFIRMED). |
| Cadence | Periodic/monthly refreshes (latest Tableau publish 2026-11-06). |
| Access method | Embedded Tableau Public dashboard (`allowDataAccess: true`; workbook download `Morbilidad HIS.twbx` is 280 MB) plus linked `Versión HISMINSA.zip` on `cloud.minsa.gob.pe`. |
| License | Footer states `Ministerio de Salud del Perú © Derechos Reservados 2026`; no open-data license declared ([REUNIS](https://www.minsa.gob.pe/reunis/)). |

#### REUNIS Egresos Hospitalarios and Emergencias Hospitalarias (SEEM)

Pages: [Emergencias Hospitalarias](https://www.minsa.gob.pe/reunis/index.asp?op=3&niv=3&tbl=3) ([SEEM_Emergencias](https://public.tableau.com/profile/api/single_workbook/SEEM_Emergencias)) and [Egresos](https://www.minsa.gob.pe/reunis/index.asp?op=3&niv=3&tbl=4) ([SEEM_Egresos_17022807857260](https://public.tableau.com/profile/api/single_workbook/SEEM_Egresos_17022807857260)).

| Attribute | Value |
|---|---|
| Geography | Department, DIRESA, and hospital/facility (`EESS`); no district filter exposed directly in the UI. |
| Time basis | Calendar month (`Año`, `Mes`, `Ene` to `Dic`), not epi-week. |
| Place basis | Treating hospital (`EESS`), not place of infection. |
| Case classes | Clinical hospital discharges (`Egresos`) and hospital emergency visits (`Emergencias`) by 3-character ICD-10 principal diagnosis (`Afección principal` / `Categoría de Enfermedades CieX`), not surveillance confirmed or probable cases. |
| Coverage | 2016 through September 2026 (`Fecha corte: 30 de setiembre de 2026`, `Fecha actualización: 27 de Octubre de 2026`; Tableau API `lastUpdateDate: 2026-10-29`). |
| Cadence | Monthly with roughly 1-month lag. |
| Access method | Embedded Tableau Public dashboards with `allowDataAccess: false` (underlying data and workbook download disabled). |
| License | Footer states `Ministerio de Salud del Perú © Derechos Reservados 2026`; no open-data license declared ([REUNIS](https://www.minsa.gob.pe/reunis/)). |

### Other national MINSA, INS, and health-sector portals

#### SINADEF open-data mortality file (MINSA on Datos Abiertos)

Package: [Información de Fallecidos SINADEF](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=informaci%C3%B3n-de-fallecidos-del-sistema-inform%C3%A1tico-nacional-de-defunciones-sinadef-ministerio); data dictionary [Diccionario_Datos_SINADEF.xlsx](https://www.datosabiertos.gob.pe/sites/default/files/Diccionario_Datos_SINADEF.xlsx); CSV [fallecidos_sinadef.csv](https://drive.minsa.gob.pe/s/PigmdwnCGEdyqos/download) (383,534,277 bytes, pipe-delimited). REUNIS also embeds a live Tableau mortality summary ([Tablero_Control_Defunciones_0](https://public.tableau.com/profile/api/single_workbook/Tablero_Control_Defunciones_0), updated 2026-11-22, `allowDataAccess: false`).

| Attribute | Value |
|---|---|
| Geography | National, down to district (`COD# UBIGEO DOMICILIO` in RENIEC-style hyphenated format such as `92-33-14-01-13-000`, plus `DEPARTAMENTO DOMICILIO`, `PROVINCIA DOMICILIO`, `DISTRITO DOMICILIO`). |
| Time basis | Daily date of death (`FECHA`, `AÑO`, `MES`). |
| Place basis | Deceased patient's domicile (`DOMICILIO`), not place of infection. |
| Case classes | Death certificates only (causes A through F coded in CIE-X); not surveillance case counts. |
| Coverage | UNCONFIRMED exact max date inside the 383 MB file without full scan, but the downloadable CSV header on `drive.minsa.gob.pe` reports `Last-Modified: Mon, 06 May 2024 02:56:50 GMT` even though Datos Abiertos metadata was modified `2026-09-15`. |
| Cadence | Open-data CSV appears stale since May 2024; REUNIS Tableau summary updates near-daily (`2026-11-22`). |
| Access method | Direct CSV download via MINSA Nextcloud (`drive.minsa.gob.pe`) linked from Datos Abiertos. |
| License | ODC-BY, `http://opendefinition.org/licenses/odc-by/`. |

#### INS interactive dengue serotypes report

Service page: [Reporte interactivo de la circulación de serotipos por dengue](https://www.gob.pe/institucion/ins/pages/41740-consultar-el-reporte-interactivo-de-la-circulacion-de-serotipos-por-dengue) (last page edit 2026-02-11; note `https://web.ins.gob.pe/` fails TLS verification with a self-signed certificate and `https://www.gob.pe/s/28169` returns HTTP 404).

| Attribute | Value |
|---|---|
| Geography | Region / department where the laboratory sample was taken (`región donde se obtuvo la muestra`); not district-level. |
| Time basis | Annual (`según año y región`) on the service description; CDC Perú's 2026 SE 44 dengue PDF (p. 14) also displays an INS serotype chart by epi-week at national level through 2026 SE 30. |
| Place basis | Sample collection region (`donde se obtuvo la muestra`), not place of infection. |
| Case classes | Laboratory-typed dengue samples (serotypes DENV-1/2/3/4) from the INS lab network, not total surveillance cases. |
| Coverage | UNCONFIRMED exact start and end dates inside the Power BI report; CDC's SE 44 PDF cites INS serotype data through 2026 SE 30. |
| Cadence | Periodic (UNCONFIRMED exact schedule). |
| Access method | Public embedded [Power BI view](https://app.powerbi.com/view?r=eyJrIjoiYWRlNDdkOWItZmYwMC00MWE4LWEyMzUtYzE2MjVlMmQwYmIxIiwidCI6ImI0NzYxY2VlLTlkYWQtNDc3MS05ZjQ3LTVmYjc4Y2MxYjRhYSIsImMiOjR9); no bulk CSV/API download documented. |
| License | No open-data license stated on `gob.pe` or the Power BI link. |

#### Other national portals and packages checked and ruled out

- `https://datosabiertos.minsa.gob.pe/` does not resolve in DNS.
- [ENFERMEDADES METAXENICAS](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=enfermedades-metaxenicas) on Datos Abiertos contains only 7 clinical/entomological PDF guides uploaded in September 2017, no tabular data.
- [MORBILIDAD](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=morbilidad) on Datos Abiertos covers 2002 to 2016 only, aggregated nationally by month and broad ICD-10 chapter (e.g., `(A90 - A99) FIEBRES VIRALES TRANSMITIDAS POR ARTROPODOS`), with no sub-national geography and no dengue-specific column.
- [Datos de Atenciones realizadas a los asegurados - SIS](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=datos-de-atenciones-realizadas-los-asegurados-sis) (ODC-BY, semiannual ZIPs 2017 through 2025 S2, district-level by month) and [Atenciones en Consulta Externa - EsSalud](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=atenciones-en-consulta-externa-essalud) (2015 to 2022, district-level by month) include neither ICD-10 diagnosis codes nor dengue fields, as verified in the [SIS data dictionary](https://www.datosabiertos.gob.pe/sites/default/files/Diccionario_Datos%20-%20DS-01%20-%20SIS%20-%20Atenciones_v2.pdf) and [EsSalud data dictionary](https://www.datosabiertos.gob.pe/sites/default/files/DICCIONARIO_DE_DATOS_CONSULTA_EXTERNA_2015_2022_0.xlsx).
- [Indicadores básicos de salud (CDC Perú)](https://www.dge.gob.pe/portalnuevo/inteligencia-sanitaria/analisis-de-situacion-de-salud-asis/inidicadores-basicos-de-salud/) publishes annual national/regional summary PDFs (2001 to 2025) and a Power BI report, not district by epi-week dengue counts.
- Regional packages on Datos Abiertos (`casos-de-dengue-en-la-región-piura-gobierno-regional-piura`, Paita hospital, and GORE San Martín) are sub-national rather than national sources (Piura is scoped in issue #5).

## Official data dictionary for `ubigeo` and `semana`

The official data dictionary for the national dengue case file is embedded as an HTML table inside the package description on [Vigilancia Epidemiológica de dengue](https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue) and returned identically by [package_show](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue). There is no separate downloadable dictionary file attached to the package.

Exact quoted dictionary rows for `ubigeo`, `semana`, and their companion spatial, temporal, and case-class fields:

- `ubigeo` (`Caracter`): DENOMINACIÓN `"Código de ubigeo del lugar probable de infección"`, VALORES `"Estandar INEI"`.
- `semana` (`Integer`): DENOMINACIÓN `"Semana de inicio de síntomas"`, VALORES blank.
- `ano` (`Integer`): DENOMINACIÓN `"Año"`, VALORES blank.
- `distrito` (`Caracter`): DENOMINACIÓN `"Lugar probable de infección"`, VALORES blank.
- `localcod` (`Caracter`): DENOMINACIÓN `"Código de localidad del lugar probable de infección"`, VALORES blank.
- `diresa` (`Caracter`): DENOMINACIÓN `"Dirección de salud que notifica"`, VALORES blank.
- `tipo_dx` (`Caracter`): DENOMINACIÓN `"Tipo de diagnóstico"`, VALORES `"C= Confirmado, P = Probable, S = Sospechoso"`.

Three verified nuances and discrepancies between the dictionary and the live CSV (`datos_abiertos_vigilancia_dengue_2000_2025_0.csv`):

1. **Dictionary wording changed in 2026**: Wayback Machine captures of the same package page on [2025-01-14](https://web.archive.org/web/20250114140233/https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue) and [2025-12-17](https://web.archive.org/web/20251217015711/https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue) listed `ubigeo` as `"Código del lugar probable de infección"` with blank `VALORES` and omitted `localcod`. The 2026 revision explicitly clarified `"Código de ubigeo del lugar probable de infección"` and `"Estandar INEI"`.
2. **Undocumented column and absent case class**: The live CSV has 15 columns including `localidad` (between `distrito` and `enfermedad`), which is mentioned in the narrative prose as `"localida"` (typo) but omitted from the HTML dictionary table. In the live CSV, `localidad` has 53,909 blank strings and 69,726 literal `"NULL"` strings; `localcod` has 149,627 blanks; `diresa` has 23 blanks. Conversely, although the dictionary lists `S = Sospechoso`, the live file contains only `C` (955,112) and `P` (110,162) and zero suspected or discarded records.
3. **Prose cadence claim is boilerplate**: The package description states `"La información del dataset se actualiza cada semana o mes, según la sección de tendencia del boletín epidemiológico, y es suministrada semanalmente por la RENACE"`, which is copied almost word-for-word from the Boletín Epidemiológico colophon ([2026 SE 37 PDF](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202637_20_145551.pdf), p. 22) and does not describe the Datos Abiertos CSV's actual annual upload cadence.

## Reporting completeness and negative notification

Peru's surveillance regulations mandate weekly reporting and negative notification internally, but **no public national source discloses which notifying units or districts reported in a given epi-week**.

What the regulatory framework establishes:
- **Directiva Sanitaria N° 046-MINSA/DGE-V.01** ([RM N° 506-2012-MINSA](https://www.dge.gob.pe/normas/rm/2012/RM506-2012.pdf), amended by [RM N° 948-2012-MINSA](https://www.dge.gob.pe/normas/rm/2012/RM948-2012.pdf) and still referenced for notification flow in Section 6.1.1.7 of NTS N° 230-MINSA/CDC-2025, [RM N° 473-2025-MINSA](https://epipublic.dge.gob.pe/uploads/normas/normas_2025_14_100517.pdf)) requires all public and private health facilities designated as Unidades Notificantes to report weekly through NOTISP/NotiWeb on Mondays, reclassify probable cases within four epi-weeks (Section 6.2.4), and submit the closed annual database by epi-week 09 of the following year (Section 6.3.2).
- **Directiva Administrativa N° 341-MINSA/CDC-2023** ([RM N° 298-2023-MINSA](https://epipublic.dge.gob.pe/uploads/normas/normas_2023_17_084629.pdf); [CDC press note](https://www.dge.gob.pe/portalnuevo/informacion-publica/prensa/cdc-peru-aprueban-directiva-administrativa-para-la-organizacion-y-funcionamiento-de-la-red-nacional-de-epidemiologia-renace/)) formalizes RENACE, which as of 2026 SE 37 comprises 10,254 health facilities across 29 regional health jurisdictions, including 8,595 Unidades Notificantes and 1,659 Unidades Informantes ([2026 SE 37 Boletín](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202637_20_145551.pdf), p. 21; the Datos Abiertos prose cites an older count of 10,272 facilities and 8,536 Unidades Notificantes).

What is published publicly:
- **Regional-only monitoring scores in the weekly Boletín Epidemiológico**: Every weekly Boletín includes `"Indicadores de monitoreo para las notificaciones de vigilancia epidemiológica en la Red Nacional de Epidemiología del Perú"` (verified in [2015 SE 52](https://www.dge.gob.pe/portal/docs/vigilancia/boletines/2015/52.pdf) p. 11, [2025 SE 53](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202553_19_162849.pdf) pp. 35 to 36, and [2026 SE 37](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202637_20_145551.pdf) pp. 20 to 21; 443 matching issues in `epipublic`). `Tabla 2` reports four percentage scores (`Oportunidad`, `Cobertura`, `Calidad del dato`, `Retroinformación`) plus a weighted total score **only at the GERESA/DIRESA/DISA/DIRIS level** (29 jurisdictions in 2026 SE 37; 32 in 2025 SE 53) and national RENACE level. Coverage and timeliness are not uniformly 100%: in 2026 SE 37 national `Cobertura` was 98.97% (Apurímac 78.00%, Ayacucho 98.00%, Cajamarca 98.00%, San Martín 96.00%) and `Oportunidad` was 97.59% (San Martín and Puno 65.00%); in 2025 SE 53 national `Cobertura` was 96.16% and `Oportunidad` was 96.72% (Lambayeque, DIRIS Lima Norte, and DIRIS Lima Sur at 65.00%).
- **Measles-rubella and PFA negative-notification indicators**: The Boletín's measles-rubella and acute flaccid paralysis (PFA) tables (verified in [2005 SE 52](https://www.dge.gob.pe/boletines/2005/52.pdf) p. 15, [2025 SE 53](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202553_19_162849.pdf) p. 25, and [2026 SE 37](https://epipublic.dge.gob.pe/uploads/boletin/boletin_202637_20_145551.pdf) p. 10) include a column `"% de oportunidad de la notificación semanal (incluye notificación negativa)"`, again aggregated only to the regional directorate level.
- **No reporting completeness in Sala Situacional PDFs**: Neither [2026 SE 44 dengue.pdf](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/SE44/dengue.pdf) nor the 281-page combined [2026 salaSE44.pdf](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/salaSE44.pdf) contains any reporting completeness or negative notification table.

What is missing publicly:
- **NotiWeb is login-gated**: `https://app7.dge.gob.pe/notiWeb/` (linked under CDC's [intranet aplicativos page](https://www.dge.gob.pe/portalnuevo/area-privada/aplicativos-para-la-vigilancia/)) redirects to `https://sso.dge.gob.pe/...`.
- **No public unit-level or district-level submission log**: Neither Datos Abiertos nor `dge.gob.pe` publishes a weekly log of which Unidades Notificantes submitted a report or filed negative notification. Public facility registries ([MINSA IPRESS 2017](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=minsa-ipress), [SUSALUD RENIPRESS 2021](https://www.datosabiertos.gob.pe/api/3/action/package_show?id=registro-nacional-de-ipress-renipress-superintendencia-nacional-de-salud-susalud), and REUNIS [Renaes](https://public.tableau.com/profile/api/single_workbook/Renaes_17004973743510)) list authorized facilities, not weekly RENACE submission status.
- **Implication for the panel**: Because public national data cannot prove that a district's notifying units reported zero cases in a given epi-week (and regional coverage/timeliness visibly dips below 100% even in pilot regions such as Lambayeque), absent district-epi-weeks in the case file cannot be recoded as verified zeros without non-public NotiWeb reporting logs (issue #14 and issue #21).

## Prior file versions

Earlier uploads of the Datos Abiertos dengue CSV survive live on the server under distinct filenames in `https://www.datosabiertos.gob.pe/sites/default/files/`. All five surviving files below were verified independently via HTTP `HEAD` and 1,500-byte head and tail `Range` requests on 2026-11-22 (2026-11-23 UTC).

| File URL | Bytes | HTTP `Last-Modified` (UTC) | Schema and format | Tail rows observed |
|---|---|---|---|---|
| [datos_abiertos_vigilancia_dengue.csv](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue.csv) | 52,731,996 | `2024-07-17 14:16:47` | Comma-delimited, 14 cols: has `localidad` and `localcod`, **no `tipo_dx`**; labels `"SEÑALES DE ALARMA"` | 2022 (e.g., epi-weeks 47, 51) |
| [datos_abiertos_vigilancia_dengue_2000_2023.csv](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2023.csv) | 81,796,352 | `2024-12-11 14:14:24` | Comma-delimited, all strings quoted, CRLF, 13 cols: **has `tipo_dx`**, drops `localidad` and `localcod`; labels `"SIGNOS DE ALARMA"` | 2023 epi-week 52 |
| [datos_abiertos_vigilancia_dengue_2000_2024.csv](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2024.csv) | 108,550,394 | `2025-12-16 20:39:10` | **Semicolon-delimited**, UTF-8 BOM, CRLF, 14 cols: restores `localidad` and `localcod`, **drops `tipo_dx`** | 2024 epi-week 52 |
| [datos_abiertos_vigilancia_dengue_2000_2025.csv](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2025.csv) | 115,735,922 | `2026-10-21 17:15:46` | Comma-delimited, 14 cols: has `localidad` and `localcod`, **no `tipo_dx`** | 2025 (unsorted tail; ends at epi-week 41) |
| [datos_abiertos_vigilancia_dengue_2000_2025_0.csv](https://www.datosabiertos.gob.pe/sites/default/files/datos_abiertos_vigilancia_dengue_2000_2025_0.csv) (currently linked) | 117,866,478 | `2026-10-22 15:14:04` | Comma-delimited, 15 cols: has `localidad`, `localcod`, and **re-adds `tipo_dx`** | 2025 (unsorted tail; full local file max is 2025 epi-week 53) |

Supporting provenance verified on the server and Wayback Machine:
- Package revisions ([node 16351 revisions](https://www.datosabiertos.gob.pe/node/16351/revisions); [package_revision_list](https://www.datosabiertos.gob.pe/api/3/action/package_revision_list?id=vigilancia-epidemiol%C3%B3gica-de-dengue)): `2023-11-22 22:11:24 UTC` (`dge_minsa`), `2024-12-11 20:13:31 UTC` (`dge_minsa`), `2025-12-16 21:16:28 UTC` (`dge_minsa`), `2025-12-16 21:18:20 UTC` (`dge_minsa`), `2025-12-17 14:19:02 UTC` (`Andrea`), and `2026-10-21 17:13:51 UTC` (`jmedina_minsa_cdc`).
- Resource revisions ([node 23482 revisions](https://www.datosabiertos.gob.pe/node/23482/revisions)): `2025-12-16 16:16 -05` (`dge_minsa`), `2025-12-17 09:19 -05` (`Andrea`), `2026-10-21 12:16 -05` (`jmedina_minsa_cdc`), and `2026-10-22 10:16 -05` (`jmedina_minsa_cdc`). Opening any past revision view (`/node/16351/revisions/{39304,46089}/view` and `/node/23482/revisions/{56116,69823}/view`) returns HTTP 403.
- Wayback Machine CDX ([CDX query](https://web.archive.org/cdx/search/cdx?url=https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue&output=json&fl=timestamp,original,statuscode)) captures the package page on `2025-01-14` (linking `_2000_2023.csv`, modified `2024-12-11`) and `2025-12-17` (linking `_2000_2024.csv`, modified `2025-12-16`); no pre-2025 captures and no archived CSV payloads exist in Wayback CDX.
- Additional filename probes returning HTTP 404: `datos_abiertos_vigilancia_dengue_0.csv`, `_2000_2021.csv`, `_2000_2022.csv`, `_2000_2023_0.csv`, `_2000_2024_0.csv`, `_2000_2025_1.csv`, `_2000_2026.csv`, and `_2000_2026_0.csv`.

Operational consequences of these surviving snapshots:
- Archiving all five surviving files (issue #2) lets the project measure **year-over-year retrospective revisions** across the 2022, 2023, 2024, and 2025 releases, and guards against silent deletion.
- Every future ingestion script must defend against schema, delimiter, BOM, quoting, column-set (`tipo_dx`, `localidad`, `localcod`), and label-string (`SEÑALES` vs `SIGNOS`) drift across releases.
- Because no intra-year weekly snapshots exist on Datos Abiertos, these files cannot measure short-horizon (1 to 4 epi-week) reporting delay or feed live weekly forecasting.

## Open questions

1. **UNCONFIRMED cause of the 2024-07-17 `Last-Modified` date on `datos_abiertos_vigilancia_dengue.csv`**: Whether that file replaced the original `2023-11-22` upload in place or reflects a server-side migration could not be confirmed because revision views return HTTP 403 and Wayback has no 2023 or 2024 captures.
2. **UNCONFIRMED time and place basis in CDC weekly PDFs**: Neither the Boletín Epidemiológico summary tables nor the Sala Situacional de Dengue case slides explicitly state whether their weekly case totals are tabulated by onset week or notification week, or whether case tables use place of infection (the 2026 SE 44 dengue PDF states `Lugar probable de infección` only on the p. 20 deaths table). Reconciling overlap totals against the Datos Abiertos file (issue #10) and inspecting the interactive CDC dashboards (issue #3) is needed to settle this.
3. **Live district by epi-week series depends on non-bulletin sources**: Because neither Datos Abiertos (annual, stops at 2025), nor the Boletín Epidemiológico (regional, 9 to 10 epi-weeks behind), nor the Sala Situacional PDFs (top 9 to 10 districts only, single latest epi-week), nor REUNIS provides a complete live district by epi-week series, live weekly updates for issue #15 depend entirely on what CDC Perú's interactive dashboards expose (issue #3), regional pilot portals (issue #5), or a MINSA transparency request (issue #21).
4. **Transparency request scope for issue #21**: To code absent district-epi-weeks honestly and support live district forecasting without scraping watermarked PDFs, any request to MINSA/CDC should ask for (a) weekly NotiWeb unit-level or district-level submission and negative-notification logs, and (b) a live weekly district by onset week (and notification week) case feed with case class and `available_at`.
5. **UNCONFIRMED full contents of REUNIS `Versión HISMINSA.zip` and INS Power BI coverage**: Only the initial archive entry (`MORBILIDAD 2019 HISMINSA.xlsx`) was verified within the 25 MB probe limit, and INS's Power BI date range was not extracted interactively; neither source can substitute for a weekly district surveillance case series regardless of year span.
