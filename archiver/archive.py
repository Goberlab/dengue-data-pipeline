# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright==1.64.1", "openpyxl==3.1.5"]
# ///
"""Snapshot CDC Perú and datosabiertos dengue sources, one source per run.

    uv run archiver/archive.py <source> [--publish REPO] [--staging DIR]

Sources: sala-diaria, observatorio, datosabiertos, sala-pdf. See archiver/README.md.

Each run fetches at most what changed since the last snapshot, validates it, and
writes the files plus a meta.json into a staging folder. With --publish it uploads
them as assets of a monthly GitHub release (`<source>-YYYY-MM`) and records the
source's state in the `archive-state` release. Any failed check exits non-zero.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")
REPO_URL = "https://github.com/Goberlab/dengue-data-pipeline"
# CDC Perú's servers accept a client that names itself.
UA_IDENTIFIED = f"Mozilla/5.0 (compatible; GoberlabDengueArchiver/0.1; +{REPO_URL})"
# datosabiertos.gob.pe answers HTTP 418 to any User-Agent that is not a plain browser string.
UA_BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

SALA_DIARIA_URL = "https://app7.dge.gob.pe/maps2/sala_diaria_dengue.html"
SALA_DIARIA_WORKBOOKS = {
    "indicadores_dengue_diario.xlsx",
    "indicadores_dengue_diario_distrito.xlsx",
    "casos_dengue_forma_clinica.xlsx",
    "defunciones_dengue.xlsx",
}
OBSERVATORIO_URL = "https://app7.dge.gob.pe/maps2/shiny_observatorio_web/"
OBSERVATORIO_CASE_CLASSES = ["CONFIRMADO", "PROBABLE"]
DATOSABIERTOS_PACKAGE = (
    "https://www.datosabiertos.gob.pe/api/3/action/package_show?id=vigilancia-epidemiol%C3%B3gica-de-dengue"
)
SALA_PDF_URL = "https://www.dge.gob.pe/portal/docs/vigilancia/sala/{year}/SE{week}/dengue.pdf"
STATE_TAG = "archive-state"


class ArchiveError(Exception):
    """A check failed: the run must fail loudly."""


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise ArchiveError(msg)


# ---------------------------------------------------------------- time


def now_stamps() -> dict:
    t = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return {
        "fetched_at_utc": t.isoformat().replace("+00:00", "Z"),
        "fetched_at_lima": t.astimezone(LIMA).isoformat(),
        "stamp": t.strftime("%Y%m%dT%H%M%SZ"),
        "month": t.strftime("%Y-%m"),
    }


def epi_week(day: dt.date) -> tuple[int, int]:
    """MINSA epi-week (same rule as CDC/MMWR): Sunday start, week 1 holds Jan 4."""

    def week1_start(year: int) -> dt.date:
        jan4 = dt.date(year, 1, 4)
        return jan4 - dt.timedelta(days=(jan4.weekday() + 1) % 7)

    year = day.year
    if day < week1_start(year):
        year -= 1
    elif day >= week1_start(year + 1):
        year += 1
    return year, (day - week1_start(year)).days // 7 + 1


# ---------------------------------------------------------------- http


def http(url: str, ua: str, method: str = "GET", headers: dict | None = None, timeout: int = 300):
    """Return (status, headers, body). 304 and 404 come back as statuses, not exceptions."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": ua, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers.items()), r.read() if method != "HEAD" else b""
    except urllib.error.HTTPError as e:
        if e.code in (304, 404):
            return e.code, dict(e.headers.items()), b""
        raise ArchiveError(f"{method} {url} -> HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise ArchiveError(f"{method} {url} -> {e.reason}") from e


def header(h: dict, name: str) -> str | None:
    return next((v for k, v in h.items() if k.lower() == name.lower()), None)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_complete(body: bytes, h: dict, url: str) -> None:
    length = header(h, "Content-Length")
    check(len(body) > 0, f"{url}: empty body")
    if length is not None:
        check(len(body) == int(length), f"{url}: truncated, got {len(body)} of {length} bytes")


# ---------------------------------------------------------------- snapshot store


class Store:
    """Staging folder plus, when publishing, monthly releases and a state release."""

    def __init__(self, source: str, staging: Path, repo: str | None):
        self.source, self.repo = source, repo
        self.stamps = now_stamps()
        self.dir = staging / source / self.stamps["stamp"]
        self.files: list[Path] = []
        self.records: list[dict] = []

    def add(self, name: str, payload: bytes, record: dict, compress: bool = False) -> None:
        """Stage one fetched file. `record` describes the fetch; sizes and hashes are added here."""
        self.dir.mkdir(parents=True, exist_ok=True)
        asset = f"{self.source}_{self.stamps['stamp']}_{name}" + (".gz" if compress else "")
        data = gzip.compress(payload, mtime=0) if compress else payload
        (self.dir / asset).write_bytes(data)
        self.files.append(self.dir / asset)
        self.records.append({"asset": asset, "bytes": len(payload), "sha256": sha256(payload), **record})

    def gh(self, *args: str, check_rc: bool = True) -> subprocess.CompletedProcess:
        r = subprocess.run(["gh", *args, "-R", self.repo], capture_output=True, text=True)
        if check_rc and r.returncode != 0:
            raise ArchiveError(f"gh {' '.join(args[:3])}: {r.stderr.strip()}")
        return r

    def ensure_release(self, tag: str, notes: str) -> None:
        if self.gh("release", "view", tag, check_rc=False).returncode == 0:
            return
        latest = ["--latest=false"] if tag == STATE_TAG else []
        r = self.gh("release", "create", tag, "--title", tag, "--notes", notes, *latest, check_rc=False)
        # a parallel job may have created it first
        if r.returncode != 0 and self.gh("release", "view", tag, check_rc=False).returncode != 0:
            raise ArchiveError(f"cannot create release {tag}: {r.stderr.strip()}")

    def load_state(self) -> dict:
        name = f"state-{self.source}.json"
        if not self.repo:
            p = self.dir.parent / name
            return json.loads(p.read_text()) if p.exists() else {}
        r = self.gh("release", "view", STATE_TAG, "--json", "assets", check_rc=False)
        if r.returncode != 0:
            if "not found" in r.stderr.lower():
                return {}
            raise ArchiveError(f"cannot read state: {r.stderr.strip()}")
        if name not in [a["name"] for a in json.loads(r.stdout)["assets"]]:
            return {}
        with tempfile.TemporaryDirectory() as d:
            self.gh("release", "download", STATE_TAG, "-p", name, "-D", d)
            return json.loads((Path(d) / name).read_text())

    def commit(self, state: dict, summary: dict) -> None:
        """Write meta.json, upload the snapshot if there is one, then save state."""
        if self.records:
            meta = {"source": self.source, **self.stamps, "files": self.records, "summary": summary,
                    "archiver": {"commit": os.environ.get("GITHUB_SHA"), "run": os.environ.get("GITHUB_RUN_ID")}}
            meta_path = self.dir / f"{self.source}_{self.stamps['stamp']}_meta.json"
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
            self.files.append(meta_path)
        state = {**state, "last_run_utc": self.stamps["fetched_at_utc"]}
        state_name = f"state-{self.source}.json"
        if not self.repo:
            self.dir.parent.mkdir(parents=True, exist_ok=True)
            (self.dir.parent / state_name).write_text(json.dumps(state, indent=2))
            return
        if self.files:
            tag = f"{self.source}-{self.stamps['month']}"
            self.ensure_release(tag, f"Snapshots of `{self.source}` fetched in {self.stamps['month']} (UTC). "
                                     f"Each snapshot is a set of assets sharing one timestamp plus a `_meta.json`. "
                                     f"See archiver/README.md.")
            self.gh("release", "upload", tag, *map(str, self.files))
        self.ensure_release(STATE_TAG, "Archiver bookkeeping: the last fingerprint seen per source. Not data.")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / state_name
            p.write_text(json.dumps(state, indent=2))
            self.gh("release", "upload", STATE_TAG, str(p), "--clobber")


# ---------------------------------------------------------------- sources


def sala_diaria(store: Store) -> dict:
    """Daily dashboard: one conditional GET of an 18 MB static HTML with everything inlined."""
    state = store.load_state()
    cond = {}
    if state.get("etag"):
        cond["If-None-Match"] = state["etag"]
    if state.get("last_modified"):
        cond["If-Modified-Since"] = state["last_modified"]
    status, h, body = http(SALA_DIARIA_URL, UA_IDENTIFIED, headers=cond)
    if status == 304:
        store.commit(state, {})
        return {"changed": False}
    check(status == 200, f"sala_diaria: HTTP {status}")
    check_complete(body, h, SALA_DIARIA_URL)
    check(len(body) > 5_000_000, f"sala_diaria: only {len(body)} bytes, expected about 18 MB")
    html = body.decode("utf-8", errors="replace")
    check(html.rstrip().endswith("</html>"), "sala_diaria: HTML does not end with </html>")
    widgets = len(re.findall(r'<script type="application/json" data-for="htmlwidget-', html))
    check(widgets >= 30, f"sala_diaria: {widgets} htmlwidget payloads, expected about 37")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    cut = re.search(r"(\d{2}-\d{2}-\d{4}) Fecha de corte", text)
    check(cut is not None, "sala_diaria: no 'Fecha de corte' found")

    validators = {"etag": header(h, "ETag"), "last_modified": header(h, "Last-Modified")}
    if sha256(body) == state.get("sha256"):  # server ignored the conditional request
        store.commit({**state, **validators}, {})
        return {"changed": False}
    store.add("sala_diaria_dengue.html", body, {"url": SALA_DIARIA_URL, **validators}, compress=True)
    found = set()
    for m in re.finditer(r"data:application/vnd\.openxmlformats[^;\"']*;base64,([A-Za-z0-9+/=]+)", html):
        name = re.search(r"download\s*=\s*(?:&#39;|'|\")([^&'\"]+)", html[m.end():m.end() + 900])
        check(name is not None, "sala_diaria: embedded workbook without a filename")
        xlsx = base64.b64decode(m.group(1))
        check(zipfile.is_zipfile(io.BytesIO(xlsx)), f"sala_diaria: {name.group(1)} is not a valid xlsx")
        store.add(name.group(1), xlsx, {"extracted_from": "sala_diaria_dengue.html"})
        found.add(name.group(1))
    check(found == SALA_DIARIA_WORKBOOKS, f"sala_diaria: workbooks found {sorted(found)}")

    summary = {"fecha_corte": cut.group(1), "htmlwidgets": widgets}
    store.commit({"etag": header(h, "ETag"), "last_modified": header(h, "Last-Modified"),
                  "sha256": sha256(body), "fecha_corte": cut.group(1)}, summary)
    return {"changed": True, **summary}


def datosabiertos(store: Store) -> dict:
    """National case file: save the package metadata and any CSV whose fingerprint changed."""
    state = store.load_state()
    status, h, body = http(DATOSABIERTOS_PACKAGE, UA_BROWSER)
    check(status == 200, f"datosabiertos package_show: HTTP {status}")
    pkg = json.loads(body)
    check(pkg.get("success") is True, "datosabiertos package_show: success is not true")
    result = pkg["result"][0] if isinstance(pkg["result"], list) else pkg["result"]
    resources = [r for r in result.get("resources", []) if str(r.get("url", "")).lower().endswith(".csv")]
    check(resources, "datosabiertos: package lists no CSV resource")

    new_state = {"package_sha256": sha256(body), "resources": dict(state.get("resources", {}))}
    if new_state["package_sha256"] != state.get("package_sha256"):
        store.add("package_show.json", body, {"url": DATOSABIERTOS_PACKAGE})

    changed = []
    for res in resources:
        url = res["url"]
        status, h, _ = http(url, UA_BROWSER, method="HEAD")
        check(status == 200, f"datosabiertos HEAD {url}: HTTP {status}")
        fp = {"content_length": header(h, "Content-Length"), "last_modified": header(h, "Last-Modified")}
        old = state.get("resources", {}).get(url, {})
        if {k: old.get(k) for k in fp} == fp:
            continue
        status, h, csv = http(url, UA_BROWSER, timeout=900)
        check(status == 200, f"datosabiertos GET {url}: HTTP {status}")
        check_complete(csv, h, url)
        head = csv[:4096].decode("utf-8-sig", errors="replace").lower()
        for col in ("ubigeo", "ano", "semana"):
            check(col in head.splitlines()[0], f"datosabiertos {url}: header lacks '{col}'")
        rows = csv.count(b"\n")
        check(rows > 100_000, f"datosabiertos {url}: only {rows} lines")
        digest = sha256(csv)
        if digest != old.get("sha256"):
            store.add(Path(url).name, csv, {"url": url, "resource_id": res.get("id"), **fp, "lines": rows},
                      compress=True)
            changed.append(Path(url).name)
        new_state["resources"][url] = {**fp, "sha256": digest}
    store.commit(new_state, {"csv_changed": changed})
    return {"changed": bool(store.records), "csv_changed": changed}


def sala_pdf(store: Store) -> dict:
    """Weekly Sala Situacional dengue PDF: fetch weeks not yet held, or whose Last-Modified moved."""
    state = store.load_state()
    held = state.get("weeks", {})
    today = dt.datetime.now(LIMA).date()
    weeks = sorted({epi_week(today - dt.timedelta(weeks=k)) for k in range(6)})  # crosses year ends
    fetched = []
    for year, w in weeks:
        key = f"{year}-SE{w:02d}"
        for label in dict.fromkeys([f"{w:02d}", str(w)]):  # early weeks may be SE1 or SE01
            url = SALA_PDF_URL.format(year=year, week=label)
            status, h, _ = http(url, UA_IDENTIFIED, method="HEAD")
            if status == 200:
                break
        if status == 404:
            continue
        check(status == 200, f"sala_pdf HEAD {url}: HTTP {status}")
        lm = header(h, "Last-Modified")
        if held.get(key, {}).get("last_modified") == lm:
            continue
        status, h, pdf = http(url, UA_IDENTIFIED)
        check(status == 200, f"sala_pdf GET {url}: HTTP {status}")
        check_complete(pdf, h, url)
        check(pdf.startswith(b"%PDF"), f"sala_pdf {url}: not a PDF")
        store.add(f"{key}_dengue.pdf", pdf, {"url": url, "last_modified": lm, "epi_week": key})
        held[key] = {"last_modified": lm, "sha256": sha256(pdf)}
        fetched.append(key)
        time.sleep(2)
    store.commit({"weeks": held}, {"fetched": fetched, "checked_through": f"{weeks[-1][0]}-SE{weeks[-1][1]:02d}"})
    return {"changed": bool(fetched), "fetched": fetched}


# Observatorio: an R Shiny app. The export only exists inside a live session, so a
# headless browser sets the inputs, presses the button, and fetches the download URL.

JS_SET_SELECT = """([id, v]) => { const el = document.getElementById(id);
  if (el.selectize) el.selectize.setValue(v); else { el.value = v; el.dispatchEvent(new Event('change')); } }"""
JS_INPUT = "id => Shiny.shinyapp.$inputValues[id]"


def _wait_idle(page, settle: float = 1.5, timeout: float = 180) -> None:
    t0, calm = time.time(), None
    while time.time() - t0 < timeout:
        if page.evaluate("document.documentElement.classList.contains('shiny-busy')"):
            calm = None
        elif calm is None:
            calm = time.time()
        elif time.time() - calm >= settle:
            return
        time.sleep(0.25)
    raise ArchiveError("observatorio: Shiny never went idle")


def _set_inputs(page, wanted: dict) -> None:
    """Set inputs and re-check until they hold: the server sometimes resets the department late."""
    for _ in range(6):
        for id_, v in wanted.items():
            if page.evaluate(JS_INPUT, id_) != v:
                if id_.endswith("sel_ano"):
                    page.evaluate("([id, v]) => { $('#' + id).data('ionRangeSlider').update({from: v[0], to: v[1]}); $('#' + id).trigger('change'); }",
                                  [id_, v])
                else:
                    page.evaluate(JS_SET_SELECT, [id_, v])
                _wait_idle(page)
        _wait_idle(page, settle=2.5)
        if all(page.evaluate(JS_INPUT, k) == v for k, v in wanted.items()):
            return
    got = {k: page.evaluate(JS_INPUT, k) for k in wanted}
    raise ArchiveError(f"observatorio: inputs would not hold: wanted {wanted}, got {got}")


def _validate_observatorio(xlsx: bytes, depa: str, case_class: str) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True)
    check("Distrito" in wb.sheetnames, f"observatorio {depa}/{case_class}: no Distrito sheet ({wb.sheetnames})")
    rows = wb["Distrito"].iter_rows(values_only=True)
    hdr = list(next(rows))
    for col in ("Departamento", "UBIGEO", "Ano", "Semana", "Tipo caso", "Casos"):
        check(col in hdr, f"observatorio {depa}/{case_class}: Distrito sheet lacks {col}")
    ix = {c: hdr.index(c) for c in hdr}
    per_district: dict[str, int] = {}
    years, last_reported, n = set(), None, 0
    for r in rows:
        n += 1
        ub, tipo = str(r[ix["UBIGEO"]]), r[ix["Tipo caso"]]
        check(re.fullmatch(r"\d{6}", ub) is not None, f"observatorio {depa}: bad UBIGEO {ub!r}")
        check(tipo in (case_class, None, "NULL"), f"observatorio {depa}: Tipo caso {tipo!r} in a {case_class} export")
        if depa != "LIMA METROPOLITANA":
            check(r[ix["Departamento"]] == depa, f"observatorio {depa}: row for {r[ix['Departamento']]!r}")
        per_district[ub] = per_district.get(ub, 0) + 1
        years.add(int(r[ix["Ano"]]))
        if tipo not in (None, "NULL"):
            wk = (int(r[ix["Ano"]]), int(r[ix["Semana"]]))
            last_reported = max(last_reported or wk, wk)
    check(n > 0 and per_district, f"observatorio {depa}/{case_class}: empty Distrito sheet")
    check(len(set(per_district.values())) == 1,
          f"observatorio {depa}/{case_class}: districts have unequal week counts")
    return {"districts": len(per_district), "rows": n, "years": [min(years), max(years)],
            "last_week_with_tipo": f"{last_reported[0]}-SE{last_reported[1]:02d}" if last_reported else None}


def observatorio(store: Store, departments: list[str] | None, force: bool) -> dict:
    from playwright.sync_api import sync_playwright

    state = store.load_state()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=UA_IDENTIFIED)
        page.goto(OBSERVATORIO_URL, wait_until="domcontentloaded", timeout=180_000)
        page.wait_for_function("window.Shiny && Shiny.shinyapp && Shiny.shinyapp.isConnected()", timeout=180_000)
        _wait_idle(page)
        page.evaluate("document.querySelector('a[data-value=\"tendencias\"]').click()")
        _wait_idle(page)
        text = page.evaluate("document.body.innerText")
        cut = re.search(r"Semana de corte\s*(\d{1,2})", text)
        check(cut is not None, "observatorio: no 'Semana de corte' on the Tendencias tab")
        cut_week = int(cut.group(1))
        last = state.get("captured_at_utc")
        age_days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(last.replace("Z", "+00:00"))).days \
            if last else None
        # a subset capture (a test, a pilot run) never stands in for the weekly national one
        if (not force and state.get("all_departments") and state.get("semana_corte") == cut_week
                and age_days is not None and age_days < 7):
            browser.close()
            store.commit(state, {})
            return {"changed": False, "semana_corte": cut_week}

        options = page.evaluate("Object.keys(document.getElementById('tendencias-sel_depa').selectize.options)")
        depas = departments or [d for d in options if d != "NACIONAL"]
        check(all(d in options for d in depas), f"observatorio: unknown department in {depas}")
        slider = page.evaluate("[...['data-min','data-max']].map(a => +document.getElementById('tendencias-sel_ano').getAttribute(a))")
        sid = page.evaluate("Shiny.shinyapp.config.sessionId")
        captured = {}
        for depa in depas:
            for case_class in OBSERVATORIO_CASE_CLASSES:
                _set_inputs(page, {"tendencias-sel_enfermedad": "dengue", "tendencias-sel_tipodx": case_class,
                                   "tendencias-sel_depa": depa, "tendencias-sel_ano": slider})
                page.click("#tendencias-btn_zona")
                _wait_idle(page, settle=2.5)
                _set_inputs(page, {"tendencias-sel_depa": depa, "tendencias-sel_tipodx": case_class})
                url = f"{OBSERVATORIO_URL}session/{sid}/download/tendencias-down_climasalud?w="
                r = page.request.get(url, timeout=300_000)
                body = r.body()
                check(r.status == 200, f"observatorio {depa}/{case_class}: HTTP {r.status}")
                check("spreadsheetml" in (r.headers.get("content-type") or ""),
                      f"observatorio {depa}/{case_class}: content-type {r.headers.get('content-type')}")
                info = _validate_observatorio(body, depa, case_class)
                check(info["years"] == slider, f"observatorio {depa}/{case_class}: years {info['years']}, asked {slider}")
                slug = re.sub(r"[^a-z0-9]+", "-", depa.lower()).strip("-")
                store.add(f"{slug}_{case_class.lower()}.xlsx", body,
                          {"department": depa, "case_class": case_class, "semana_corte": cut_week, **info})
                captured[f"{depa}/{case_class}"] = info["rows"]
                time.sleep(3)
        browser.close()
    summary = {"semana_corte": cut_week, "exports": len(captured), "slider_years": slider}
    if departments:  # keep the last national capture's fingerprint; this one was partial
        store.commit(state, summary)
    else:
        store.commit({"semana_corte": cut_week, "captured_at_utc": store.stamps["fetched_at_utc"],
                      "all_departments": True, "departments": depas}, summary)
    return {"changed": True, **summary}


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", choices=["sala-diaria", "observatorio", "datosabiertos", "sala-pdf"])
    ap.add_argument("--publish", metavar="OWNER/REPO", help="upload to this repo's releases (default: stage only)")
    ap.add_argument("--staging", type=Path, default=Path("data/archive-staging"))
    ap.add_argument("--departments", help="observatorio: comma-separated subset, e.g. PIURA,TUMBES")
    ap.add_argument("--force", action="store_true", help="observatorio: capture even if the cut week is unchanged")
    a = ap.parse_args()
    store = Store(a.source, a.staging, a.publish)
    try:
        if a.source == "sala-diaria":
            out = sala_diaria(store)
        elif a.source == "datosabiertos":
            out = datosabiertos(store)
        elif a.source == "sala-pdf":
            out = sala_pdf(store)
        else:
            out = observatorio(store, a.departments.split(",") if a.departments else None, a.force)
    except ArchiveError as e:
        print(f"ARCHIVE FAILED [{a.source}]: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"source": a.source, **store.stamps, **out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
