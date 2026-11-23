# District reference geography (2000 to 2026)

## Short answer

Use INEI's 6-digit UBIGEO from [SISCONCODE](https://webapp.inei.gob.pe:8443/sisconcode/publico.htm) (2026 version, 1,893 districts) as the canonical district spine and name-to-UBIGEO crosswalk, paired with an explicit alias table and a 4-DIRIS plus Lima Región crosswalk for department 15. Use [INEI IDE `DISTRITO.gpkg`](https://ide.inei.gob.pe/files/Distrito.rar) (1,890 districts, EPSG:4326) for pilot and historical boundaries (100% pilot coverage; 3 post-2021 non-pilot districts missing), and [Copernicus DEM GLO-30 Public](https://registry.opendata.aws/copernicus-dem/) on AWS Open Data (free, open, attribution-only) for elevation. Use INEI's versioned yearly district population releases stamped with each publication's `available_at` (Boletín Especial 18 for 2000 to 2015, Boletín Especial 26 and 27 plus the 31 December 2025 2018 to 2026 Excel update), noting that CDC Perú's live 2026 daily dashboard diverges sharply from INEI at district level (Tumbes +22.6%) and appears to draw on MINSA OGTI/REUNIS tables. Definitive 2025 census results were published between May and October 2026 and show large district revisions (up to -19.9% in Piura district), but INEI has not yet released post-2025 population projections.

## UBIGEO lineage

### District counts from 2000 to 2026

Peru's administrative count rose from 1,821 districts on 1 January 2000 to 1,893 districts by July 2026, a net increase of 72 districts across 26 years. Every institutional figure reconciles exactly when accounting for cutoff dates and one temporary statistical merge (`120699` Mazamari - Pangoa):

| Cutoff date | Provinces (incl. Callao) | Districts | Source |
| :--- | ---: | ---: | :--- |
| 11 Jul 1993 (Census 1993) | 188 | 1,793 | [INEI Boletín Especial 18, dp001.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp001.xls) |
| 1 Jan 2000 (start of panel window) | 194 | 1,821 | Computed from 1,793 plus 28 creations from Jul 1993 to Dec 1999 in [dp004.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp004.xls) |
| 31 Dec 2000 | 194 | 1,826 | 1,821 plus 5 creations in May to Sep 2000 in [dp004.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp004.xls) |
| Feb 2001 to Oct 2004 | 194 | 1,828 | 1,826 plus 2 creations in Feb 2001 in [dp004.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp004.xls) |
| 2005 (after Datem del Marañón) | 195 | 1,831 | [INEI Boletín Especial 18, dp002.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp002.xls) |
| 21 Oct 2007 (Census 2007) | 195 | 1,833 | [INEI Censo 2025 National Publication](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/publicaciones/Publicacion_nacional_de_los_censos_nacionales.pdf), Cuadro 1.1; [dp001.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp001.xls) |
| 30 Sep 2009 (Boletín Especial 18) | 195 | 1,834 | Incorporates Bagua (Ley 28884, 2006/2008); [dp001.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp001.xls) |
| 2010 (SISCONCODE version 1) | 195 | 1,837 codes (1,838 legal) | 1,834 plus 4 laws in Jun to Jul 2010, minus 1 due to `120699` merge; [SISCONCODE v1 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/1/1/1/null/null/null) |
| 2014 (SISCONCODE version 3) | 196 | 1,851 | Adds province Putumayo (`1608`), 13 new districts (incl. `200115`), restores `120604` and `120606`; [SISCONCODE v3 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/3/1/1/null/null/null) |
| 2015 (SISCONCODE version 4) | 196 | 1,867 | Adds 16 districts; [SISCONCODE v4 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/4/1/1/null/null/null) |
| 2016 / Census 2017 (SISCONCODE version 5) | 196 | 1,874 | Adds 7 districts; [SISCONCODE v5 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/5/1/1/null/null/null); [Boletín Especial 26](https://www.gob.pe/institucion/inei/informes-publicaciones/6855012-peru-estimaciones-y-proyecciones-de-poblacion-por-departamento-provincia-y-distrito-2018-2020) |
| 2021 (SISCONCODE version 6) | 196 | 1,890 | Adds 16 districts (Dec 2020 to Jun 2021); [SISCONCODE v6 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/6/1/1/null/null/null); [Boletín Especial 27](https://www.gob.pe/institucion/inei/informes-publicaciones/3464927-peru-proyecciones-de-poblacion-total-segun-departamento-provincia-y-distrito-2018-2022) |
| 2022 (SISCONCODE version 7) | 196 | 1,891 | Adds Alto Trujillo (`130112`, Ley 31644, 15 Dec 2022); [SISCONCODE v7 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/7/1/1/null/null/null) |
| Jul 2025 / Jun 2026 (SISCONCODE version 8) | 196 | 1,892 | Adds Santa Rosa de Loreto (`160405`, Ley 32403, 3 Jul 2025); [SISCONCODE v8 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/8/1/1/null/null/null); [INEI 2018 to 2026 Excel](https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026) |
| 15 Jul 2026 (SISCONCODE version 9) | 196 | 1,893 | Adds Sangani (`120307`, Ley 32729, 15 Jul 2026); [SISCONCODE v9 export](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/9/1/1/null/null/null); [Censo 2025 National Tabulados](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx) |

This count also reconciles exactly with PCM SDOT's statement of 64 districts created between 2002 and 2025 on [Demarca Perú](https://geosdot.servicios.gob.pe/geoportal/creacionesdistritales): 72 creations from 2000 to 2026 minus 7 created in 2000 and 2001 minus 1 created in 2026 (Sangani) equals 64. Note that SISCONCODE export URLs require starting a session cookie at [publico.htm](https://webapp.inei.gob.pe:8443/sisconcode/publico.htm) before requesting the `/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/{versionId}/1/1/null/null/null` endpoint.

### Pilot regions (Piura, Tumbes, Lambayeque)

Across the 116 pilot districts in 2026 (65 in Piura, 38 in Lambayeque, 13 in Tumbes), exactly two districts were created between 2000 and 2026, and no UBIGEO codes were recoded:

1. **Piura (`20`): 64 districts in 2000 to 65 in 2013 to 2026.** The only creation is **Veintiséis de Octubre (`200115`)**, province of Piura, split from **Piura (`200101`)** by Ley N° 29991 (promulgated 2 February 2013, published in El Peruano on 3 February 2013), as documented in [INEI Boletín Especial 26](https://cdn.www.gob.pe/uploads/document/file/8199290/6855012-peru-estimaciones-y-proyecciones-de-poblacion-por-departamento-provincia-y-distrito-2018-2020.pdf) (pages 31 and 108). It first appears in SISCONCODE version 3 (2014). Two boundary-sanitation laws affecting Piura provinces (without creating new districts) were enacted in 2026: Ley N° 32659 (16 June 2026, Paita) and Ley N° 32715 (6 July 2026, Sechura), recorded in the Anexo sheet of [Censo 2025 `Indicadores_demograficos.xlsx`](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx).
2. **Tumbes (`24`): 12 districts in 2000 to 13 in 2006 to 2026.** **Canoas de Punta Sal (`240203`)**, province of Contralmirante Villar, was created from **Zorritos (`240201`)** and **Casitas (`240202`)** by Ley N° 28707 (promulgated 3 April 2006, published 11 April 2006), documented in [Boletín Especial 18 `dp004.xls`](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp004.xls) and [`dispositivos.pdf`](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/dispositivos.pdf) (item 71). Any 2000 to 2006 panel backtest for Tumbes must account for this split just as 2000 to 2016 Piura panels account for Veintiséis de Octubre.
3. **Lambayeque (`14`): 38 districts throughout 2000 to 2026.** Zero creations since 2000; its last five creations (Cayaltí, Pátapo, Pomalca, Pucalá and Tumán) occurred under Ley N° 26921 on 31 January 1998 ([dp004.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp004.xls), items 134 to 138). Two boundary-sanitation laws were enacted in 2026: Ley N° 32652 (14 June 2026, Chiclayo) and Ley N° 32694 (3 July 2026, Ferreñafe), which slightly shifted Censo 2025 counts in Chiclayo ([Indicadores_demograficos.xlsx](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx), Anexo).

### Complete list of district creations, splits and recodings since 2000

#### Province creations causing UBIGEO recodings and temporary merges

Three non-creation UBIGEO code changes occurred between 2000 and 2026 and must be handled in historical joins (especially for Loreto and Junín in national surveillance files):

1. **Datem del Marañón (`1607`, Loreto), 2005:** Ley N° 28593 (promulgated 1 August 2005, published 2 August 2005) created province Datem del Marañón (`1607`) and new district Andoas (`160706`), transferring five existing districts out of Alto Amazonas (`1602`): Barranca (`160701`), Cahuapanas (`160702`), Manseriche (`160703`), Morona (`160704`) and Pastaza (`160705`). Sources: [dp003.xls](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp003.xls), [dispositivos.pdf](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/dispositivos.pdf) (item 70), [SISCONCODE v1](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/1/1/1/null/null/null). Exact pre-2005 `1602xx` district codes for those five districts were not pulled from a pre-2005 INEI table (UNCONFIRMED; verify in ticket #11 against the historical case file).
2. **Mazamari - Pangoa (`120699`, Satipo, Junín), 2010 to 2014:** In [SISCONCODE v1 (2010)](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/1/1/1/null/null/null), INEI replaced Mazamari (`120604`) and Pangoa (`120606`) with a single combined code `120699` ("Mazamari - Pangoa") due to a boundary dispute; [SISCONCODE v3 (2014)](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/3/1/1/null/null/null) dropped `120699` and restored `120604` and `120606`.
3. **Putumayo (`1608`, Loreto), 2014:** Ley N° 30186 (promulgated 10 April 2014, published 6 May 2014) created province Putumayo (`1608`), recoding Putumayo from `160109` (Maynas) to `160801` and Teniente Manuel Clavero from `160114` (Maynas) to `160803`, and creating two new districts, Rosa Panduro (`160802`) and Yaguas (`160804`). Sources: [Boletín Especial 26](https://cdn.www.gob.pe/uploads/document/file/8199290/6855012-peru-estimaciones-y-proyecciones-de-poblacion-por-departamento-provincia-y-distrito-2018-2020.pdf) (pages 32 and 108) and diff of [SISCONCODE v1](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/1/1/1/null/null/null) vs [v3](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/3/1/1/null/null/null).

#### All 72 districts created from 2000 to 2026

Verified directly against [Boletín Especial 18 `dp004.xls`](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/cuadros/dp004.xls) and [`dispositivos.pdf`](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/dispositivos.pdf) (2000 to 2009), [Boletín Especial 26](https://cdn.www.gob.pe/uploads/document/file/8199290/6855012-peru-estimaciones-y-proyecciones-de-poblacion-por-departamento-provincia-y-distrito-2018-2020.pdf) pages 31 to 32 and 107 to 110 (2010 to 2016), footnotes 2 to 22 of [INEI 2018 to 2026 Excel](https://cdn.www.gob.pe/uploads/document/file/8261096/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026.xlsx) (2020 to 2025), [Censo 2025 `Indicadores_demograficos.xlsx`](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx) Anexo (2026), and all eight [SISCONCODE exports](https://webapp.inei.gob.pe:8443/sisconcode/publico.htm):

| UBIGEO | District | Province, Department | Law | Published in El Peruano | Parent district(s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `100111` | Pillco Marca | Huánuco, Huánuco | Ley 27258 | 2000-05-07 | Huánuco |
| `050115` | Jesús Nazareno | Huamanga, Ayacucho | Ley 27281 | 2000-06-07 | Ayacucho |
| `090118` | Ascensión | Huancavelica, Huancavelica | Ley 27284 | 2000-06-09 | Huancavelica |
| `170204` | Huepetuhe | Manu, Madre de Dios | Ley 27285 | 2000-06-10 | Madre de Dios; Camanti (Cusco) |
| `050408` | Llochegua | Huanta, Ayacucho | Ley 27346 | 2000-09-15 | Sivia |
| `101108` | Choras | Yarowilca, Huánuco | Ley 27414 | 2001-02-03 | Chavinillo |
| `230110` | Coronel Gregorio Albarracín Lanchipa | Tacna, Tacna | Ley 27415 | 2001-02-03 | Tacna |
| `160114` -> `160803` | Teniente Manuel Clavero | Maynas -> Putumayo, Loreto | Ley 28362 | 2004-10-20 | Putumayo |
| `211210` | San Pedro de Putina Punco | Sandia, Puno | Ley 28509 | 2005-05-14 | San Juan del Oro; Limbani |
| `160706` | Andoas | Datem del Marañón, Loreto | Ley 28593 | 2005-08-02 | Pastaza |
| `240203` | **Canoas de Punta Sal (pilot)** | Contralmirante Villar, Tumbes | Ley 28707 | 2006-04-11 | Zorritos (`240201`); Casitas (`240202`) |
| `250107` | Manantay | Coronel Portillo, Ucayali | Ley 28753 | 2006-06-06 | Callería; Campo Verde; Nueva Requena; Yarinacocha |
| `010201` | Bagua | Bagua, Amazonas | Ley 28884 | 2006-09-23 (recorded 2008) | La Peca |
| `090511` | Cosme | Churcampa, Huancavelica | Ley 29538 | 2010-06-08 | Anco |
| `100112` | Yacus | Huánuco, Huánuco | Ley 29540 | 2010-06-15 | Margos; Quisqui |
| `190308` | Constitución | Oxapampa, Pasco | Ley 29541 | 2010-06-15 | Puerto Bermúdez |
| `050509` | Samugari | La Mar, Ayacucho | Ley 29558 | 2010-07-18 (UNCONFIRMED vs 16 Jul in Congress summary; Boletín 26 p. 107 states 18 Jul) | San Miguel |
| `200115` | **Veintiséis de Octubre (pilot)** | Piura, Piura | Ley 29991 | 2013-02-03 | Piura (`200101`) |
| `050116` | Andrés Avelino Cáceres Dorregaray | Huamanga, Ayacucho | Ley 30013 | 2013-04-28 | Ayacucho; Jesús Nazareno and Huamanga districts |
| `050510` | Anchihuay | La Mar, Ayacucho | Ley 30086 | 2013-09-29 | Anco |
| `050409` | Canayre | Huanta, Ayacucho | Ley 30087 | 2013-09-29 | Llochegua |
| `160802` | Rosa Panduro | Putumayo, Loreto | Ley 30186 | 2014-05-06 | Putumayo |
| `160804` | Yaguas | Putumayo, Loreto | Ley 30186 | 2014-05-06 | Putumayo; Torres Causana |
| `070107` | Mi Perú | Prov. Const. del Callao, Callao | Ley 30197 | 2014-05-17 | Ventanilla; Ancón (Lima) |
| `050410` | Uchuraccay | Huanta, Ayacucho | Ley 30221 | 2014-07-11 | Huanta; Sivia |
| `080911` | Inkawasi | La Convención, Cusco | Ley 30265 | 2014-11-19 | Vilcabamba |
| `090719` | Quichuas | Tayacaja, Huancavelica | Ley 30278 | 2014-12-03 | Colcabamba |
| `080912` | Villa Virgen | La Convención, Cusco | Ley 30279 | 2014-12-03 | Vilcabamba |
| `090720` | Andaymarca | Tayacaja, Huancavelica | Ley 30280 | 2014-12-03 | Colcabamba |
| `030220` | José María Arguedas | Andahuaylas, Apurímac | Ley 30295 | 2014-12-28 | Andahuaylas |
| `250304` | Neshuya | Padre Abad, Ucayali | Ley 30310 | 2015-03-17 | Irazola |
| `250305` | Alexander Von Humboldt | Padre Abad, Ucayali | Ley 30310 | 2015-03-17 | Irazola; Tournavista (Huánuco) |
| `050411` | Pucacolpa | Huanta, Ayacucho | Ley 30320 | 2015-04-28 | Ayahuanco; Tintay Puncu (Huancavelica) |
| `120609` | Vizcatán del Ene | Satipo, Junín | Ley 30346 | 2015-10-03 | Pangoa |
| `080913` | Villa Kintiarina | La Convención, Cusco | Ley 30349 | 2015-10-15 | Kimbiri |
| `230111` | La Yarada Los Palos | Tacna, Tacna | Ley 30358 | 2015-11-08 | Tacna |
| `100704` | La Morada | Marañón, Huánuco | Ley 30360 | 2015-11-12 | Cholón; Cochabamba |
| `100607` | Pucayacu | Leoncio Prado, Huánuco | Ley 30376 | 2015-12-08 | José Crespo y Castillo; Alto Biavo (San Martín) |
| `100608` | Castillo Grande | Leoncio Prado, Huánuco | Ley 30377 | 2015-12-08 | Rupa-Rupa |
| `100705` | Santa Rosa de Alto Yanajanca | Marañón, Huánuco | Ley 30378 | 2015-12-08 | Cholón |
| `100113` | San Pablo de Pillao | Huánuco, Huánuco | Ley 30379 | 2015-12-08 | Chinchao |
| `050412` | Chaca | Huanta, Ayacucho | Ley 30387 | 2015-12-17 | Santillana |
| `090721` | Roble | Tayacaja, Huancavelica | Ley 30388 | 2015-12-17 | Tintay Puncu |
| `090722` | Pichos | Tayacaja, Huancavelica | Ley 30391 | 2015-12-20 | Huaribamba; Pazos |
| `030609` | Rocchacc | Chincheros, Apurímac | Ley 30392 | 2015-12-20 | Ongoy |
| `030610` | El Porvenir | Chincheros, Apurímac | Ley 30393 | 2015-12-20 | Ongoy |
| `100609` | Pueblo Nuevo | Leoncio Prado, Huánuco | Ley 30440 | 2016-05-28 | José Crespo y Castillo |
| `090723` | Santiago de Tucuma | Tayacaja, Huancavelica | Ley 30445 | 2016-05-29 | Pampas |
| `030611` | Los Chankas | Chincheros, Apurímac | Ley 30455 | 2016-06-14 | Huaccana |
| `050511` | Oronccoy | La Mar, Ayacucho | Ley 30457 | 2016-06-15 | Chungui |
| `080914` | Megantoni | La Convención, Cusco | Ley 30481 | 2016-07-06 | Echarate |
| `100610` | Santo Domingo de Anda | Leoncio Prado, Huánuco | Ley 30491 | 2016-07-24 | José Crespo y Castillo |
| `211105` | San Miguel | San Román, Puno | Ley 30492 | 2016-07-27 | Juliaca; Calapuja; Caminaca; Pusi; Caracoto |
| `090724` | Lambras | Tayacaja, Huancavelica | Ley 31092 | 2020-12-19 | Surcubamba; Huachocolpa |
| `221006` | Santa Lucía | Tocache, San Martín | Ley 31128 | 2021-03-04 | Uchiza; Tocache |
| `050512` | Unión Progreso | La Mar, Ayacucho | Ley 31130 | 2021-03-05 | Anco |
| `090725` | Cochabamba | Tayacaja, Huancavelica | Ley 31132 | 2021-03-09 | Tintay Puncu |
| `250306` | Huipoca | Padre Abad, Ucayali | Ley 31133 | 2021-03-09 | Padre Abad |
| `050413` | Putis | Huanta, Ayacucho | Ley 31134 | 2021-03-09 | Santillana |
| `050513` | Río Magdalena | La Mar, Ayacucho | Ley 31135 | 2021-03-09 | Samugari |
| `050514` | Ninabamba | La Mar, Ayacucho | Ley 31137 | 2021-03-16 | San Miguel |
| `050515` | Patibamba | La Mar, Ayacucho | Ley 31138 | 2021-03-16 | San Miguel |
| `250307` | Boquerón | Padre Abad, Ucayali | Ley 31141 | 2021-03-18 | Padre Abad |
| `080915` | Kumpirushiato | La Convención, Cusco | Ley 31142 | 2021-03-18 | Echarate |
| `080916` | Cielo Punco | La Convención, Cusco | Ley 31162 | 2021-04-07 | Kimbiri |
| `080917` | Manitea | La Convención, Cusco | Ley 31163 | 2021-04-07 | Kimbiri |
| `030612` | Ahuayro | Chincheros, Apurímac | Ley 31186 | 2021-05-02 | Huaccana |
| `080918` | Unión Asháninka | La Convención, Cusco | Ley 31197 | 2021-05-18 | Pichari |
| `180107` | San Antonio | Mariscal Nieto, Moquegua | Ley 31216 | 2021-06-15 | Moquegua |
| `130112` | Alto Trujillo | Trujillo, La Libertad | Ley 31644 (typo "31664" in footnote 18, "31644" in footnote 19 of INEI Excel) | 2022-12-15 | El Porvenir; Huanchaco (also adjusts La Esperanza, Florencia de Mora) |
| `160405` | Santa Rosa de Loreto | Mariscal Ramón Castilla, Loreto | Ley 32403 | 2025-07-03 | Yavarí |
| `120307` | Sangani | Chanchamayo, Junín | Ley 32729 | 2026-07-15 | Perené (exact parent district in Ley 32729 UNCONFIRMED from El Peruano full text) |

Note on INEI vs RENIEC UBIGEO: Peru has two incompatible 6-digit UBIGEO systems. INEI orders departments alphabetically (placing Callao at `07`), whereas RENIEC places Callao at `24`, shifting department prefixes alphabetically after Cajamarca (for example, Cercado de Lima is `150101` in INEI and `140101` in RENIEC). Surveillance and statistical tables from INEI and MINSA/CDC use INEI UBIGEO; any table sourced from RENIEC, ONPE or JNE must be converted via a dedicated equivalence table before joining.

### Name-to-UBIGEO crosswalk and Lima DIRIS split

Both CDC Perú's live daily dengue dashboard ([sala_diaria_dengue.html](https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html)) and INEI's Censo 2025 downloadable national tabulados ([Indicadores_demograficos.xlsx](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx)) omit the 6-digit `ubigeo` column and identify districts by name only.

An exhaustive collision check on [SISCONCODE 2026 (v9, 1,893 districts)](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/9/1/1/null/null/null) after ASCII/diacritic/punctuation/case normalization shows:

- **Distrito alone is not unique:** 100 normalized district names repeat across Peru, covering 257 districts (most frequent: `SANTA ROSA` 10 times, `SAN ANTONIO` 6, `SANTA CRUZ` 5, `PUEBLO NUEVO` 5, `MIRAFLORES` 4). Thirteen of the 116 pilot districts share their name with another Peruvian district (`La Victoria`, `Lagunas`, `Santa Rosa`, `Pueblo Nuevo`, `Salas`, `San José`, `La Unión`, `Huancabamba`, `Buenos Aires`, `Bellavista`, `Salitral`).
- **`(departamento, distrito)` is STILL not unique:** 13 pairs collide across provinces within the same department (26 districts total). Crucially, one collision sits inside the pilot: **Piura / Salitral** exists in both Morropón (`200406`) and Sullana (`200608`). Four collisions sit inside Lima (`Miraflores` `150122` vs `151021`, `San Luis` `150134` vs `150514`, `San Antonio` `150513` vs `150716`, `Laraos` `150712` vs `151018`).
- **`(departamento, provincia, distrito)` is 100% unique:** 0 collisions across all 1,893 districts in 2026 (and across all historical SISCONCODE snapshots from 2010 to 2026).

**Recommended crosswalk spine:** Use [SISCONCODE 2026 (`versionId=9`)](https://webapp.inei.gob.pe:8443/sisconcode/web/ubigeo/listaBusquedaUbigeoPorUbicacionGeograficaXls/9/1/1/null/null/null) (unioned with pre-2014 retired codes `160109`, `160114`, `120699` for historical lookups) normalized by Unicode NFKD diacritic stripping, uppercasing, punctuation removal and whitespace collapse, plus an explicit alias table.

**Empirical verification against CDC's live daily dashboard:** Testing this normalized `(departamento, provincia, distrito)` crosswalk against all 565 active district rows embedded in [sala_diaria_dengue.html](https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html) (cutoff 20 November 2026, after mapping `CALLAO / CALLAO` to `CALLAO / PROV CONST DEL CALLAO`) matched **560 of 565 rows (99.1%)**, including 100% of pilot rows. The exact 5 unmatched rows were two spelling variants between CDC and INEI:

- `HUANUCO / LEONCIO PRADO / DANIEL ALOMIAS ROBLES` (CDC) vs `Daniel Alomía Robles` (`100602`, SISCONCODE).
- `ICA / NAZCA / {CHANGUILLO, EL INGENIO, NAZCA, VISTA ALEGRE}` (CDC, province and district with `Z`) vs `Nasca` (`1103`, `110301`, SISCONCODE with `S`).

Additional verified spelling variants across INEI's own files ([pob_2018_2026.xlsx](https://cdn.www.gob.pe/uploads/document/file/8261096/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026.xlsx) vs SISCONCODE 2026) and MINSA texts that the alias table should absorb include: stripping trailing footnote markers (for example `AHUAYRO 15/`, `EL PORVENIR 18/ 20/`), `SAN FRANCISCO DEL YESO` vs `San Francisco de Yeso` (`010517`), `SAN FRANCISCO DE RAVACAYCO` vs `San Francisco de Rivacayco` (`050707`), `QUISQUI` vs `Quisqui (Kichki)` (`100106`), `CERCADO DE LIMA` vs `Lima` (`150101`), `LURIGANCHO-CHOSICA` vs `Lurigancho` (`150118`), and accent drift across SISCONCODE years (`Veintiseis`/`Veintiséis`, `Jose`/`José`, `La Union`/`La Unión`).

#### How Lima is split: four DIRIS plus Lima Región vs merged `LIMA`

In [sala_diaria_dengue.html](https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html), CDC uses both representations inside the same page:

- The **department summary table** splits department `15` into five health jurisdictions: `DIRIS LIMA CENTRO`, `DIRIS LIMA ESTE`, `DIRIS LIMA NORTE`, `DIRIS LIMA SUR`, and `LIMA REGIÓN`.
- The **district table** merges all 80 active Lima districts under a single `Departamento = 'LIMA'` label, distinguishing Lima Metropolitana (`Provincia = 'LIMA'`) from Lima Región (`Provincia` in `BARRANCA`, `CAÑETE`, `CANTA`, `HUARAL`, `HUAROCHIRI`, `HUAURA`, `OYON`, etc.).
- By contrast, INEI's Censo 2025 tabulados ([Indicadores_demograficos.xlsx](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx)) split department `15` into two top-level rows: `LIMA METROPOLITANA` (43 districts, `1501xx`) and `REGIÓN LIMA` (128 districts across 9 provinces, `1502xx` to `1510xx`).

Under MINSA's [Resolución Ministerial N° 467-2017-MINSA](https://www.gob.pe/institucion/minsa/normas-legales/189346-467-2017-minsa) (16 June 2017, Manual de Operaciones de las DIRIS) and the institutional portals of [DIRIS Lima Norte](https://www.gob.pe/institucion/dirislimanorte/institucional), [DIRIS Lima Este](https://www.gob.pe/institucion/dirislimaeste/institucional), [DIRIS Lima Centro](https://www.gob.pe/institucion/dirislimacentro/institucional), [DIRIS Lima Sur](https://www.gob.pe/institucion/dirislimasur/institucional) and [DIRESA Lima](https://www.gob.pe/institucion/regionlima-diresa/institucional), all 171 districts of department `15` map cleanly to the five health jurisdictions:

| Health jurisdiction | District count | Exact INEI UBIGEO codes (from SISCONCODE 2026) |
| :--- | ---: | :--- |
| DIRIS Lima Centro | 14 | `150101` Lima, `150105` Breña, `150113` Jesús María, `150115` La Victoria, `150116` Lince, `150120` Magdalena del Mar, `150121` Pueblo Libre, `150122` Miraflores, `150130` San Borja, `150131` San Isidro, `150132` San Juan de Lurigancho, `150134` San Luis, `150136` San Miguel, `150141` Surquillo |
| DIRIS Lima Norte | 9 | `150102` Ancón, `150106` Carabayllo, `150110` Comas, `150112` Independencia, `150117` Los Olivos, `150125` Puente Piedra, `150128` Rímac, `150135` San Martín de Porres, `150139` Santa Rosa |
| DIRIS Lima Este | 7 | `150103` Ate, `150107` Chaclacayo, `150109` Cieneguilla, `150111` El Agustino, `150114` La Molina, `150118` Lurigancho, `150137` Santa Anita |
| DIRIS Lima Sur | 13 | `150104` Barranco, `150108` Chorrillos, `150119` Lurín, `150123` Pachacámac, `150124` Pucusana, `150126` Punta Hermosa, `150127` Punta Negra, `150129` San Bartolo, `150133` San Juan de Miraflores, `150138` Santa María del Mar, `150140` Santiago de Surco, `150142` Villa El Salvador, `150143` Villa María del Triunfo |
| Lima Región (DIRESA Lima) | 128 | All districts in provinces `1502` Barranca, `1503` Cajatambo, `1504` Canta, `1505` Cañete, `1506` Huaral, `1507` Huarochirí, `1508` Huaura, `1509` Oyón, `1510` Yauyos |

Note: DIRIS Lima Norte (9 districts) and DIRIS Lima Este (7 districts) were verified verbatim on their `gob.pe` institutional pages; the PDF attached to RM 467-2017-MINSA on `gob.pe` is a scanned image without embedded text, so the DIRIS Lima Centro (14) and DIRIS Lima Sur (13) district rosters were cross-checked against public MINSA summaries and verified numerically against CDC's 2026 DIRIS population denominators (within 0.6% to 2.3% of INEI 2026 sums). Confirming each of those 27 assignments directly from the scanned RM 467-2017-MINSA annex remains a minor follow-up check.

## Boundaries

Peruvian official spatial sources separate **referential census polygons** (published by INEI for full national coverage) from **legally saneated boundary segments** (registered by PCM SDOT in RENLIM, which do not yet form closed polygons for every district):

| Source | Endpoint / format | Snapshot & district count | CRS | Legal status & license |
| :--- | :--- | :--- | :--- | :--- |
| **INEI IDE bulk download (recommended)** | [Distrito.rar](https://ide.inei.gob.pe/files/Distrito.rar) containing `DISTRITO.gpkg` (28 MB GeoPackage) | `last_change` 2026-03-06; **1,890 districts** (`fuente`: V Censo Nacional Económico). Covers 100% of pilot (116/116); missing `130112`, `160405`, `120307` | EPSG:4326 (WGS 84) | Referential/censal boundaries. Explicit spatial license on `ide.inei.gob.pe` UNCONFIRMED; governed broadly by [DS N° 016-2017-PCM](https://www.gob.pe/institucion/pcm/normas-legales/292314-016-2017-pcm) (free public open data with attribution) |
| **INEI GeoServer WFS** | [Interoperabilidad:ig_distrito](https://geoespacial.inei.gob.pe/geoserver/Interoperabilidad/ows?service=WFS&version=1.0.0&request=GetCapabilities) (GeoJSON, GML, Shapefile via WFS) | Same **1,890 districts** (`V Censo Nacional Economico`) | EPSG:4326 | Same as above; open unauthenticated WFS |
| **INEI Censo 2025 Geoportal** | [geoservercpv2025.inei.gob.pe](https://censos2025.inei.gob.pe/resultados/geoportal/poblacion-vivienda) (`cpv_resultados_v2:limites_administrativos_v2`) | Censo 2025 frame (1,892 or 1,893 districts, exact layer count UNCONFIRMED) | UNCONFIRMED | Direct WFS returns HTTP 401; no public bulk GeoPackage/Shapefile download found on `censos2025.inei.gob.pe` |
| **PCM SDOT / RENLIM** | [RENLIM_POSTGIS FeatureServer](https://services5.arcgis.com/S6BNcv6j9C2h1n1d/arcgis/rest/services/RENLIM_POSTGIS/FeatureServer?f=json) and [WFS](https://dservices5.arcgis.com/S6BNcv6j9C2h1n1d/arcgis/services/RENLIM_POSTGIS/WFSServer?request=getcapabilities&service=wfs); [Visor SDOT](https://geosdot.servicios.gob.pe/visor/) | 849 point nodes (`renlim_nodos`) and 1,289 polyline segments (`renlim_limites_tramos`), not closed district polygons | Web Mercator / PostGIS | Legally binding registered segments. Visor SDOT explicitly states its displayed district polygons are INEI's referential census boundaries, with no legal demarcation effect |
| **IGN (`idep.gob.pe`) & `datosabiertos.gob.pe`** | [idep.gob.pe descarga](https://www.idep.gob.pe/geovisor/df2/descarga.html) links district limits to [datosabiertos resource ac9bc756](https://www.datosabiertos.gob.pe/dataset/resource/ac9bc756-e41f-4c08-b4a3-a168a8874e98); also hosts [cartointerpretables.rar](https://www.idep.gob.pe/descargas_CN/limites/cartointerpretables.rar) (Last-Modified 14 May 2018) | Exact district count and snapshot on `datosabiertos.gob.pe` UNCONFIRMED (site returned HTTP 418 WAF to automated requests) | UNCONFIRMED | Open data portal under [DS N° 016-2017-PCM](https://www.gob.pe/institucion/pcm/normas-legales/292314-016-2017-pcm); GEOIDEP established by [DS N° 069-2011-PCM](https://www.gob.pe/institucion/pcm/normas-legales/292464-069-2011-pcm). Specific license tag on the resource UNCONFIRMED |
| **GeoGPS Perú (third-party mirror)** | [geogpsperu.com/p/descargas.html](https://www.geogpsperu.com/p/descargas.html) | Mirrors INEI/IGN shapefiles (not primary) | WGS 84 / UTM | Third-party aggregator; no formal redistribution license; use only as convenience cross-check |

**Recommendation for the pipeline:** Adopt **INEI IDE `DISTRITO.gpkg`** (1,890 districts, EPSG:4326) as the primary boundary file. It is directly downloadable without authentication, is a modern single-file GeoPackage, includes 6-digit `ubigeo`, `nombdep`, `nombprov`, `nombdist`, and covers all 116 pilot districts cleanly (including Veintiséis de Octubre `200115` and Canoas de Punta Sal `240203`). For national runs beyond 2021, flag the 3 missing post-2021 districts (`130112` Alto Trujillo, `160405` Santa Rosa de Loreto, `120307` Sangani) and upgrade once INEI publishes a public 1,893-district GeoPackage from Censo 2025 (or once the IGN/PCM `datosabiertos.gob.pe` file is checked in a browser). Note that even CDC Perú's own Leaflet map inside [sala_diaria_dengue.html](https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html) renders `NA` labels for 5 active districts including `Santa Rosa de Loreto` (`160405`) and `Bellavista` (`200602`, Piura).

## Elevation

**Recommended source: Copernicus DEM GLO-30 Public (`COP-DEM-GLO-30-F`)** accessed as Cloud-Optimized GeoTIFFs (COGs) on [AWS Registry of Open Data (`s3://copernicus-dem-30m`)](https://registry.opendata.aws/copernicus-dem/) (no AWS account required, `--no-sign-request`) or [Microsoft Planetary Computer STAC (`cop-dem-glo-30`)](https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-30).

- **Technical properties:** 1 arc-second (~30 m) Digital Surface Model derived from DLR/Airbus TanDEM-X radar acquisitions (2011 to 2015), void-filled, horizontal CRS WGS84-G1150 (EPSG:4326), vertical datum EGM2008 (EPSG:3855, meters), documented in the [Copernicus DEM Product Handbook](https://object.cloud.sdsc.edu/v1/AUTH_opentopography/www/metadata/Copernicus_metadata.pdf) and [CDSE COP-DEM collection page](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).
- **Verified Peru coverage:** Checking AWS [`tileList.txt`](https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt) (26,450 global tiles) confirms 222 1-degree tiles covering Peru's bounding box (`S00` to `S19`, `W068` to `W082`), including 100% of Piura, Tumbes and Lambayeque (`S03` to `S07`, `W079` to `W081`). Peru is not on the German SatDSiG restricted countries list in [ESA's CCM Data Access Restrictions (v1.2, April 2025)](https://dataspace.copernicus.eu/sites/default/files/media/files/2025-06/ccm_data_access_restrictions_v2.pdf).
- **License:** Governed by the *Licence for the use of the Copernicus WorldDEM-30* (`COP-DEM-GLO-30-F`) in [ESA's official licence document (21 February 2025)](https://dataspace.copernicus.eu/sites/default/files/media/files/2025-06/copernicus_contributing_mission_data_access_v2_cop_dem_licenses.pdf). Rights are worldwide, time-unlimited, free of charge, and non-exclusive for reproduction, distribution, communication to the general public, and adaptation/combination with other data (no non-commercial restriction). Derived outputs must carry the attribution notice: `"produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"` plus a liability disclaimer (Article 6).

**Secondary fallback: NASA SRTMGL1 v003** ([NASA Earthdata](https://www.earthdata.nasa.gov/data/catalog/lpcloud-srtmgl1-003), DOI `10.5067/MEASURES/SRTM/SRTMGL1.003`), 1 arc-second (~30 m), acquired February 2000, vertical datum EGM96, void-filled from ASTER GDEM2/GMTED2010. Under [NASA Earthdata Data Use Guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance), NASA data are freely accessible without commercial restriction (citation requested), but LP DAAC requires an Earthdata login and SRTM is older with lower vertical fidelity in steep Andean valleys. National IGN elevation services on [IDEP ArcGIS REST](https://www.idep.gob.pe/geoportal/rest/services/DATOS_GEOESPACIALES/ExtractDEMPERU12Task/GPServer?f=json) expose an asynchronous extraction GP task and a cached slope map (`MAPA_BASE/PERU_DEMPP`) with no open COG bulk mirror or verified open license.

**Aggregation note for Peru:** Because Andean and Piedmont districts (including upland Piura provinces like Ayabaca and Huancabamba) combine inhabited valleys with high mountain ridges, district elevation summaries should store distribution statistics (mean, median, min, max, standard deviation) and, if adopted in ticket #18, a population-weighted elevation summary (for instance weighted by INEI centros poblados or gridded population) rather than plain polygon mean alone.

## Population

INEI publishes mid-year (30 June) district population estimates and projections in discrete waves tied to national censuses. Each release's publication date sets its `available_at` in the panel so historical issue weeks never leak later demographic revisions:

| Series / release | Years covered | Base census | Districts | Publication date (`available_at`) | Verified primary URL |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Boletín Especial N° 16 (*Proyecciones de Población por Años Calendario según Departamentos, Provincias y Distritos, 1990-2005*) | 1990 to 2005 | Census 1993 | UNCONFIRMED (~1,828) | Jan 2002 (UNCONFIRMED directly from INEI PDF; cited in bibliographic catalogs) | Primary INEI URL not retrieved (UNCONFIRMED) |
| **Boletín Especial N° 18** (*Estimaciones y Proyecciones de Población por Sexo, Según Departamento, Provincia y Distrito, 2000-2015*) | 2000 to 2015 | Census 2007 | 1,834 (cutoff Oct 2009) | **December 2009** (`2009-12-31`, signed "Lima, Diciembre 2009") | [INEI Biblioineipub lib0842](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/index.htm) and [presenta.htm](https://proyectos.inei.gob.pe/web/biblioineipub/bancopub/est/lib0842/presenta.htm) |
| Boletín Especial N° 21 (*Población Total y Edades Quinquenales, 2005-2015*) | 2005 to 2015 | Census 2007 | 1,834 (UNCONFIRMED) | 2010 (exact date UNCONFIRMED) | Primary INEI URL not retrieved (UNCONFIRMED) |
| **2016 to 2017 district gap** | 2016 to 2017 | None published by INEI | N/A | No official INEI district projection bulletin found bridging 2016 to 2017 (Boletín 18 ended at 2015; Census 2017 definitive results came out in Oct 2018) | Gap confirmed across [INEI Compendio 71202](https://www.gob.pe/institucion/inei/colecciones/71202-estimaciones-y-proyecciones-de-poblacion-nacional-departamental-provincial-y-distrital) |
| **Boletín Especial N° 26** (*Estimaciones y Proyecciones de Población por Departamento, Provincia y Distrito, 2018-2020*) | 2018 to 2020 | Census 2017 | 1,874 (cutoff Dec 2019) | **15 January 2020** (`2020-01-15`, PDF cover "Enero 2020") | [gob.pe 6855012](https://www.gob.pe/institucion/inei/informes-publicaciones/6855012-peru-estimaciones-y-proyecciones-de-poblacion-por-departamento-provincia-y-distrito-2018-2020) and [PDF](https://cdn.www.gob.pe/uploads/document/file/8199290/6855012-peru-estimaciones-y-proyecciones-de-poblacion-por-departamento-provincia-y-distrito-2018-2020.pdf) |
| **Boletín Especial N° 27** (*Proyecciones de Población Total según Departamento, Provincia y Distrito, 2018-2022*) | 2018 to 2022 | Census 2017 | 1,890 (cutoff Dec 2021) | **15 April 2022** (`2022-04-15`) | [gob.pe 3464927](https://www.gob.pe/institucion/inei/informes-publicaciones/3464927-peru-proyecciones-de-poblacion-total-segun-departamento-provincia-y-distrito-2018-2022) and [Anexo 1 XLSX](https://cdn.www.gob.pe/uploads/document/file/5501252/3464927-anexo-1.xlsx) |
| **INEI 2018 to 2026 Excel update** (*Población Total Proyectada al 30 de Junio de cada año, 2018-2026*) | 2018 to 2026 | Census 2017 (extended for MEF FONCOMUN) | 1,892 (cutoff Jul 2025) | **31 December 2025** (`2025-12-31`) | [gob.pe 6894980](https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026) and [XLSX](https://cdn.www.gob.pe/uploads/document/file/8261096/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026.xlsx) |

Additional departmental/national releases in [INEI Compendio 71202](https://www.gob.pe/institucion/inei/colecciones/71202-estimaciones-y-proyecciones-de-poblacion-nacional-departamental-provincial-y-distrital) establish the macro envelope: Boletín de Análisis Demográfico N° 38 (national 1950 to 2070, 15 May 2019), Boletín Especial N° 24 (national 1950 to 2050, 15 July 2019), Boletín de Análisis Demográfico N° 39 (departmental 1995 to 2030, 15 October 2019), and [Boletín Especial N° 25](https://www.gob.pe/institucion/inei/informes-publicaciones/6855196-peru-estimaciones-y-proyecciones-de-poblacion-departamental-por-anos-calendario-y-edad-simple-1995-2030) (departmental 1995 to 2030 by single age, 15 January 2020).

Key ingestion and `available_at` details verified directly from the downloaded workbooks:

- **Consistency across post-2017 releases:** For 2018 to 2022, national totals (`31,562,130` to `33,396,698`), pilot departmental totals, and pilot district figures (including `200101` Piura and `200115` Veintiséis de Octubre) are identical across Boletín 26, Boletín 27 and the December 2025 2018 to 2026 Excel, and departmental 2018 to 2026 totals match Boletín Especial N° 25 (`34,660,114` for Peru in 2026, `2,195,231` for Piura, `1,382,858` for Lambayeque, `273,604` for Tumbes). Only districts split after 2018 (18 districts) or affected by boundary adjustments (such as Bella Unión/Acarí in 2024) changed.
- **Annual FONCOMUN updates:** The [gob.pe 6894980](https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026) page states INEI updates and validates these district projections at the end of each year for MEF's FONCOMUN allocation; however, intermediate 2022 to 2024 annual editions (covering 2023, 2024, 2025) are no longer individually listed in Compendio 71202 (their exact historical `available_at` dates are UNCONFIRMED).
- **Parser traps in `pob_2018_2026.xlsx`:** Eighteen post-2018 districts contain literal Spanish text strings such as `"Distrito creado en 2021"` (59 cells total) in pre-creation year columns instead of nulls, and 20+ district names carry trailing footnote numbers (for example `"SANTA ROSA DE LORETO 22/"`). The workbook also carries an explicit `Nota Técnica`: *"Las proyecciones de población 2018-2026 constituyen información preliminar y de carácter referencial, hasta que se disponga de los resultados definitivos del Censo 2025."*
- **No sex or age breakdown at district level:** INEI states on [gob.pe 6894980](https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026) that post-2017 provincial and district projections cover total population only (both sexes combined), due to subnational migration volatility.

## CDC's denominator

To test whether CDC Perú uses INEI's 2018 to 2026 projections directly for its official cumulative incidence rate (`TIA`, cases per 100,000 inhabitants), we extracted the embedded department/DIRIS table (27 rows) and district table (565 active districts) from CDC's live daily dashboard ([sala_diaria_dengue.html](https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html), cutoff 20 November 2026) and back-calculated each unit's implied denominator as `cases * 100,000 / TIA`:

| Geography | CDC 2026 cases | CDC 2026 TIA | Implied CDC 2026 pop | INEI 2026 proj (`pob_2018_2026.xlsx`) | CDC vs INEI 2026 | Censo 2025 Total (`Cuadro 1`) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Perú (Total)** | 118,106 | 340.91 | 34,644,334 | 34,660,114 | -0.05% | 34,157,732 |
| **Piura (dept)** | 20,119 | 916.61 | 2,194,936 | 2,195,231 | -0.01% | 2,115,215 |
| **Lambayeque (dept)** | 19,454 | 1,406.00 | 1,383,642 | 1,382,858 | +0.06% | 1,404,633 |
| **Tumbes (dept)** | 3,283 | 978.94 | **335,363** | **273,604** | **+22.57%** | **256,691** |
| DIRIS Lima Centro | 1,978 | 67.30 | 2,939,079 | 2,873,870 | +2.27% | 2,845,131 |
| DIRIS Lima Este | 755 | 42.10 | 1,793,349 | 1,833,598 | -2.20% | 1,714,668 |
| DIRIS Lima Norte | 4,984 | 154.12 | 3,233,844 | 3,286,978 | -1.62% | 3,073,010 |
| DIRIS Lima Sur | 2,445 | 94.33 | 2,591,964 | 2,575,648 | +0.63% | 2,508,966 |
| Lima Región | 623 | 60.32 | 1,032,825 | 1,048,585 | -1.50% | 1,014,908 |
| `200101` Piura (dist) | 1,098 | 542.47 | 202,408 | 197,373 | +2.55% | 155,566 |
| `200115` Veintiséis de Octubre | 1,703 | 846.99 | 201,065 | 214,280 | -6.17% | 206,998 |
| `200104` Castilla | 1,950 | 979.53 | 199,075 | 210,227 | -5.31% | 193,614 |
| `200602` Bellavista (Sullana) | 819 | 1,628.23 | 50,300 | 39,854 | +26.21% | 38,343 |
| `140101` Chiclayo (dist) | 5,134 | 1,741.44 | 294,813 | 299,442 | -1.55% | 270,739 |
| `140116` Cayaltí | 1,186 | 6,791.11 | 17,464 | 14,481 | +20.60% | 18,052 |
| `240101` Tumbes (dist) | 1,542 | 1,249.19 | 123,440 | 122,386 | +0.86% | 114,011 |
| `240202` Casitas (Tumbes) | 23 | 328.99 | 6,991 | 2,898 | +141.24% | 2,680 |
| `240302` Aguas Verdes (Tumbes) | 218 | 622.93 | 34,996 | 20,911 | +67.36% | 19,374 |
| `240301` Zarumilla (Tumbes) | 301 | 688.99 | 43,687 | 29,008 | +50.60% | 24,909 |
| `240203` Canoas de Punta Sal | 18 | 163.87 | 10,984 | 9,443 | +16.32% | 7,634 |

**Critical finding:** CDC Perú does **not** plug INEI's `pob_2018_2026.xlsx` straight into its district incidence rates. While CDC's national total (34.64M vs 34.66M), Piura total (-0.01%) and Lambayeque total (+0.06%) sit right on top of INEI's 2026 projection, **Tumbes is +22.6% higher** (with all 13 active Tumbes districts summing to 335,364, matching CDC's departmental figure of 335,363), and individual districts inside Piura and Lambayeque diverge by -8% to +26% from INEI (for example Veintiséis de Octubre -6.2%, Bellavista +26.2%, Cayaltí +20.6%).

The institutional source behind MINSA's sectoral denominators is **MINSA OGTI / REUNIS** ([minsa.gob.pe/reunis](https://www.minsa.gob.pe/reunis/), established by [RM N° 350-2015-MINSA](https://www.gob.pe/institucion/minsa/normas-legales/194604-350-2015-minsa), 1 June 2015), which publishes annual "Población Estimada" and "Población Asignada por EESS" tables (also mirrored on [MINSA REUNIS Tableau Public](https://public.tableau.com/app/profile/minsa.reunis/viz/Poblacion_EESS_2025/PoblacionAsignada)) built from INEI projections but adjusted and validated with DIRIS and DIRESA/GERESA statistics offices. Because `minsa.gob.pe/reunis` is gated behind Cloudflare and CDC's weekly PDFs ([dengue.pdf SE 44 2026](https://www.dge.gob.pe/portal/docs/vigilancia/sala/2026/SE44/dengue.pdf) and [Boletín Epidemiológico 2026](https://epipublic.dge.gob.pe/uploads/boletin/boletin_2026_30_112436.pdf)) either timed out mid-stream or lacked extractable text, **direct numerical confirmation that REUNIS 2026 equals CDC's exact 335,363 Tumbes and district figures remains UNCONFIRMED**.

**Pipeline design implication:** If the goal is matching CDC's published official `TIA` rates (especially in Tumbes and individual Piura/Lambayeque districts), INEI's public Excel alone will not reproduce them; the pipeline will need MINSA OGTI/REUNIS's annual district population table (via manual download or ticket #21) alongside INEI's official series as a separate versioned column/source in the panel.

## The 2025 census

### Status and release timeline

**Yes: Peru's 2025 census (*Censos Nacionales 2025: XIII de Población, VIII de Vivienda y IV de Comunidades Indígenas*) has been executed and its definitive district results are published.** Verified release milestones:

- **Fieldwork:** August to October 2025, with census recovery in November (and December per INEI press release), documented on [INEI Campaign 92656](https://www.gob.pe/institucion/inei/campa%C3%B1as/92656-censos-nacionales-2025-xiii-de-poblacion-viii-de-vivienda-y-iv-de-comunidades).
- **29 May 2026 (`available_at = 2026-05-29`):** First national results released ([INEI Press Release 1399446](https://www.gob.pe/institucion/inei/noticias/1399446-inei-poblacion-del-peru-totalizo-34-millones-157-mil-732-habitantes-al-2025)). Total population: **34,157,732** (32,706,028 censada plus 1,451,704 estimated omitted, a 4.25% omission rate).
- **10 July 2026 (`available_at = 2026-07-10`):** Provincial and district results released for **1,892 districts** using the RENLIM territorial division as of 11 June 2026 ([INEI Press Release 1417313](https://www.gob.pe/institucion/inei/noticias/1417313-censos-nacionales-2025-lima-metropolitana-continua-siendo-la-provincia-mas-poblada)), accompanied by interactive [REDATAM 2025](https://redatamcpv2025.inei.gob.pe/) and departmental PDFs on [censos2025.inei.gob.pe/publicaciones](https://censos2025.inei.gob.pe/publicaciones) including [Piura](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/publicaciones/CPV%202025%20-%20PIURA.pdf) (dated July 2026, PDF created 3 August 2026), [Lambayeque](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/publicaciones/CPV%202025%20-%20LAMBAYEQUE.pdf) (dated July 2026, created 3 August 2026) and [Tumbes](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/publicaciones/CPV%202025%20-%20TUMBES.pdf) (dated August 2026, created 1 September 2026).
- **October 2026 (exact public release day UNCONFIRMED):** INEI updated the territorial cutoff to **15 July 2026**, incorporating 26 boundary-sanitation laws enacted between 13 June and 6 July 2026 plus **Ley N° 32729 (Sangani, 15 July 2026)**, bringing the census frame to **1,893 districts**. Both the 102-page [National Publication PDF](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/publicaciones/Publicacion_nacional_de_los_censos_nacionales.pdf) (PDF creation date 29 October 2026) and the machine-readable national Excel workbook [Indicadores_demograficos.xlsx](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx) (modified 2 October 2026) use this 1,893-district frame. `Cuadro N° 1` of `Indicadores_demograficos.xlsx` reports **Población Total (censada + omitida)**, **Población Censada**, and **Población Omitida** by sex for all 1,893 districts (including Sangani at 32,908 total and Santa Rosa de Loreto at 4,459 total).

### Impact on denominators and post-census projection status

**Post-2025-census population projections do not exist yet** as of 22 November 2026. [INEI Compendio 71202](https://www.gob.pe/institucion/inei/colecciones/71202-estimaciones-y-proyecciones-de-poblacion-nacional-departamental-provincial-y-distrital) contains no post-2025 projection bulletins, and INEI's latest yearly series remains the 31 December 2025 `pob_2018_2026.xlsx` (based on Census 2017). For timing context, after Census 2017 definitive results were published in October 2018, INEI took 7 to 12 months to release national/departmental projections (May to October 2019) and 15 months to release the first district projection bulletin (Boletín Especial 26 on 15 January 2020); a similar schedule puts re-based 2017 to 2025 intercensal estimates and 2026+ district projections in 2027 (exact INEI publication calendar UNCONFIRMED).

Comparing Censo 2025 **Población Total** (`Cuadro N° 1` of [Indicadores_demograficos.xlsx](https://proyectos.inei.gob.pe/dir-segmentacion-ci/postcensal/prod/adjuntos/censos-2025/descarga_datos/tabulados/00/poblacion/Indicadores_demograficos.xlsx)) against INEI's 2017-based 2025 projection ([pob_2018_2026.xlsx](https://cdn.www.gob.pe/uploads/document/file/8261096/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026.xlsx)) reveals modest national drift but **large district-level revisions in the pilot**:

| Geography | INEI 2025 projection | Censo 2025 Total (incl. omission) | Censo 2025 Censada | Revision (Total vs proj) |
| :--- | ---: | ---: | ---: | ---: |
| Perú | 34,350,244 | 34,157,732 | 32,706,028 | -0.56% |
| **Piura (dept)** | 2,172,710 | 2,115,215 | 2,089,044 | -2.65% |
| **Lambayeque (dept)** | 1,372,301 | 1,404,633 | 1,361,522 | +2.36% |
| **Tumbes (dept)** | 270,134 | 256,691 | 250,997 | -4.98% |
| `200101` Piura | 194,198 | 155,566 | 153,676 | **-19.89%** |
| `200115` Veintiséis de Octubre | 210,015 | 206,998 | 204,411 | -1.44% |
| `200104` Castilla | 205,967 | 193,614 | 191,177 | -6.00% |
| `200601` Sullana | 198,198 | 195,448 | 193,088 | -1.39% |
| `140101` Chiclayo | 298,094 | 270,739 | 262,915 | **-9.18%** |
| `240101` Tumbes | 121,016 | 114,011 | 111,473 | -5.79% |
| `240203` Canoas de Punta Sal | 9,124 | 7,634 | 7,517 | **-16.33%** |
| `240202` Casitas | 2,898 | 2,680 | 2,660 | -7.52% |

Two immediate rules follow for the panel:

1. **Strict `available_at` gating:** Backtests with an `issue week` prior to 10 July 2026 must never use Censo 2025 district counts. When INEI publishes post-2025 intercensal revisions (2017 to 2025) and forward projections, store them as a new version stamped with their publication `available_at` rather than overwriting the 2017-based series.
2. **Use `Población Total`, not `Población Censada`, for incidence denominators:** Because omission varies across departments (1.24% in Piura, 2.22% in Tumbes, 3.07% in Lambayeque, 4.25% nationally), using `Población Censada` systematically inflates incidence rates in higher-omission areas relative to INEI projections, which always project total population including omission.

## Open questions

1. **Exact source of CDC Perú's district denominators (ticket #21 / manual check):** `minsa.gob.pe/reunis` blocked automated fetches behind Cloudflare. A human or browser download of REUNIS's 2025 and 2026 district "Población Estimada" / "Población Asignada" Excel tables is needed to confirm whether REUNIS matches CDC's implied 335,363 Tumbes and district denominators, and to learn whether historical annual REUNIS files (2000 to 2026) can be obtained cleanly or requested from MINSA under ticket #21.
2. **2016 to 2017 district population bridge:** INEI Boletín Especial 18 ends at 2015 and Boletín Especial 26 starts at 2018. Ticket #14 and ticket #21 should confirm whether MINSA/REUNIS or an INEI FONCOMUN file supplies official 2016 and 2017 district denominators (and their original `available_at`), or whether the panel must interpolate/carry forward for 2016 to 2017 issue weeks until Boletín 26 arrived in January 2020.
3. **2000 to 2009 historical `available_at` and pre-2005 Loreto codes (ticket #11):** Boletín Especial 18 was published in December 2009; locating an accessible copy of Boletín Especial 16 (1990 to 2005, published ~2002) would let early-2000s issue weeks use contemporaneous denominators. Ticket #11 should also verify which pre-2005 `1602xx` codes appear in the historical case file before Datem del Marañón (`1607`) was created in 2005, and when Canoas de Punta Sal (`240203`, created 2006) first appears in the case file.
4. **Post-2021 national boundaries and `datosabiertos.gob.pe` IGN/PCM layer:** INEI IDE `DISTRITO.gpkg` (1,890 districts) is complete for the pilot (116/116), but lacks Alto Trujillo (`130112`), Santa Rosa de Loreto (`160405`) and Sangani (`120307`). A browser check of [datosabiertos.gob.pe resource ac9bc756](https://www.datosabiertos.gob.pe/dataset/resource/ac9bc756-e41f-4c08-b4a3-a168a8874e98) and monitoring `censos2025.inei.gob.pe` for a public 1,893-district GeoPackage will confirm its district count, cutoff date and explicit license string.
5. **Exact public release date of Censo 2025 1,893-district tabulados and DIRIS scan verification:** `Indicadores_demograficos.xlsx` shows file modification on 2 October 2026 and `Publicacion_nacional_de_los_censos_nacionales.pdf` shows PDF creation on 29 October 2026, but no gob.pe press release confirms their exact publication date for `available_at`. Similarly, verifying the DIRIS Lima Centro (14) and DIRIS Lima Sur (13) district rosters against the scanned annex of RM 467-2017-MINSA (or a text-based MINSA DIRIS table) will finalize the Lima crosswalk.
6. **Elevation aggregation choice (ticket #18):** Confirm whether the panel stores multiple zonal statistics from Copernicus DEM GLO-30 (mean, median, min, max) plus population-weighted elevation for steep Andean districts.
