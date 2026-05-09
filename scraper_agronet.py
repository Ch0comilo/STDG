"""
AGRONET EVA Scraper
Fetches municipal agricultural statistics from the AGRONET public API.

Usage:
    python scraper_agronet.py                   # discover codes, then fetch all
    python scraper_agronet.py --probe-only       # discover codes and print them, no data fetch
    python scraper_agronet.py --codes 10010101   # fetch specific codes only
    python scraper_agronet.py --output my.csv    # custom output file
"""

import argparse
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd

# Fix Windows console so ñ and accented chars print correctly
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/json",
    "Referer": "https://agronet.gov.co/estadisticas/agricola",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

BASE_STATS = "https://agronet.gov.co/api/agronet-eva-api/agricola-municipal-estadisticas"

# Codes confirmed to exist (extend as you find more via browser devtools)
KNOWN_CODES = {
    "10010101": "CACAO",
    "10010102": "CAFÉ",
    "10010201": "CAÑA AZUCARERA",
    "10010301": "PALMA DE ACEITE",
    "10010401": "PLÁTANO",
    "10010402": "BANANO",
    "10010501": "FIQUE",
    "10010601": "CAUCHO",
    "10010701": "PIÑA",
    "10010801": "AGUACATE",
    "10010901": "MANGO",
    "10011001": "MARACUYÁ",
    "10011101": "MORA",
    "10020101": "ARROZ RIEGO",
    "10020102": "ARROZ SECANO MECANIZADO",
    "10020103": "ARROZ SECANO MANUAL",
    "10020201": "MAÍZ TECNIFICADO",
    "10020202": "MAÍZ TRADICIONAL",
    "10020301": "FRIJOL",
    "10020401": "ALGODÓN",
    "10020501": "PAPA",
    "10020601": "YUCA",
    "10020701": "SORGO",
    "10020801": "SOYA",
    "10020901": "TRIGO",
    "10021001": "CEBADA",
    "10021101": "TABACO RUBIO",
    "10021102": "TABACO NEGRO",
}


def probe_one(code: str) -> tuple[str, int]:
    """Return (code, row_count) — 0 means no data or error."""
    url = f"{BASE_STATS}?cod_cultivo={code}"
    try:
        r = SESSION.get(url, timeout=15)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == "success":
                return code, len(d.get("data") or [])
    except Exception:
        pass
    return code, 0


def _probe_batch(candidates: list[str], workers: int) -> dict[str, int]:
    """Run probe_one over a batch in parallel. Returns {code: row_count} for hits."""
    hits: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(probe_one, c): c for c in candidates}
        for f in as_completed(futures):
            code, count = f.result()
            if count > 0:
                hits[code] = count
    return hits


def discover_codes(workers: int = 16) -> dict[str, str]:
    """
    Hierarchical 4-stage sweep so we don't miss prefixes like 07, 08, etc.

    Code structure: PP QQ RR VV  (each pair is 2 digits, zero-padded)
      PP = commodity group  (01–20)
      QQ = sub-group        (01–30)
      RR = crop class       (01–15)
      VV = variety/type     (01–10)

    Stage 1: find valid PP        → test PP010101  (20 probes)
    Stage 2: for each PP, find QQ → test PPQQ0101  (up to 30 each)
    Stage 3: for each PP+QQ, find RR               (up to 15 each)
    Stage 4: for each PP+QQ+RR, find VV            (up to 10 each)
    """
    valid: dict[str, str] = {}

    # ---------- Stage 1: find valid PP ----------
    stage1 = [f"{p:02d}010101" for p in range(1, 21)]
    print(f"Stage 1 — probing {len(stage1)} first-level prefixes...")
    hits1 = _probe_batch(stage1, workers)
    valid_pp = sorted({c[:2] for c in hits1})
    print(f"  Valid PP prefixes: {valid_pp}\n")

    # ---------- Stage 2: find valid QQ for each PP ----------
    stage2 = [
        f"{pp}{q:02d}0101"
        for pp in valid_pp
        for q in range(1, 31)
    ]
    print(f"Stage 2 — probing {len(stage2)} PP+QQ combinations...")
    hits2 = _probe_batch(stage2, workers)
    valid_ppqq = sorted({c[:4] for c in hits2})
    print(f"  Valid PP+QQ: {valid_ppqq}\n")

    # ---------- Stage 3: find valid RR for each PP+QQ ----------
    stage3 = [
        f"{ppqq}{r:02d}01"
        for ppqq in valid_ppqq
        for r in range(1, 16)
    ]
    print(f"Stage 3 — probing {len(stage3)} PP+QQ+RR combinations...")
    hits3 = _probe_batch(stage3, workers)
    valid_ppqqrr = sorted({c[:6] for c in hits3})
    print(f"  Valid PP+QQ+RR: {valid_ppqqrr}\n")

    # ---------- Stage 4: find valid VV for each PP+QQ+RR ----------
    stage4 = [
        f"{ppqqrr}{v:02d}"
        for ppqqrr in valid_ppqqrr
        for v in range(1, 11)
    ]
    print(f"Stage 4 — probing {len(stage4)} full codes...")
    hits4 = _probe_batch(stage4, workers)

    for code, count in sorted(hits4.items()):
        name = KNOWN_CODES.get(code, "")
        valid[code] = name
        print(f"  FOUND {code} ({name if name else '?'}) — {count:,} rows")

    # Also keep any known codes that weren't caught by the sweep
    for code in KNOWN_CODES:
        if code not in valid:
            _, count = probe_one(code)
            if count > 0:
                valid[code] = KNOWN_CODES[code]

    return valid


def fetch_crop(cod_cultivo: str, retries: int = 3) -> list[dict]:
    url = f"{BASE_STATS}?cod_cultivo={cod_cultivo}"
    for attempt in range(1, retries + 1):
        try:
            r = SESSION.get(url, timeout=30)
            r.raise_for_status()
            payload = r.json()
            if payload.get("status") == "success":
                return payload.get("data") or []
            return []
        except requests.RequestException as exc:
            print(f"    [attempt {attempt}/{retries}] {cod_cultivo}: {exc}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codes", nargs="+", help="Crop codes to fetch (skips discovery)")
    parser.add_argument("--probe-only", action="store_true", help="Discover codes and print, don't fetch data")
    parser.add_argument("--output", default="data/agronet_eva.csv")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between data requests")
    parser.add_argument("--workers", type=int, default=16, help="Parallel workers for probing")
    args = parser.parse_args()

    # --- Determine which codes to use ---
    if args.codes:
        crops = {c: KNOWN_CODES.get(c, "") for c in args.codes}
        print(f"Using {len(crops)} user-specified code(s).")
    else:
        crops = discover_codes(workers=args.workers)
        print(f"\nDiscovered {len(crops)} valid code(s): {sorted(crops)}\n")

    if args.probe_only:
        for code, name in sorted(crops.items()):
            print(f"  {code}  {name}")
        return

    if not crops:
        print("No valid codes found. Exiting.")
        sys.exit(1)

    # --- Fetch full data for each crop ---
    print(f"\nFetching full data for {len(crops)} crop(s)...\n")
    all_records: list[dict] = []
    failed: list[str] = []

    for cod, name in sorted(crops.items()):
        label = f"{cod} ({name})" if name else cod
        print(f"  {label} ...", end=" ", flush=True)
        records = fetch_crop(cod)
        if records:
            all_records.extend(records)
            print(f"{len(records):,} rows")
        else:
            failed.append(cod)
            print("no data / error")
        time.sleep(args.delay)

    if not all_records:
        print("No data collected.")
        sys.exit(1)

    # --- Build and save DataFrame ---
    df = pd.DataFrame(all_records)

    if "anio" in df.columns:
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    for col in ["area_sembrada", "area_cosechada", "produccion", "rendimiento"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"\n{'='*50}")
    print(f"Rows saved : {len(df):,}")
    print(f"File       : {args.output}")
    print(f"Columns    : {list(df.columns)}")
    if "anio" in df.columns:
        years = sorted(df["anio"].dropna().unique().tolist())
        print(f"Years      : {years[0]} – {years[-1]}")
    if "producto" in df.columns:
        print(f"Crops      : {sorted(df['producto'].unique().tolist())}")
    if failed:
        print(f"Failed     : {failed}")


if __name__ == "__main__":
    main()
