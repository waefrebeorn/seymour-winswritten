#!/usr/bin/env python3
"""
Seymour Wins — WEEKLY VOLUME SPLITTER
=====================================================================
The annual multiverse PDF for each year is laid out as:
    page 0  = cover
    then 366 days, each = 31 pages (1 real + 30 AU)
    => total = 1 + 366*31

This script splits each annual PDF into 52 (or 53) WEEKLY volumes that
chronicle the year week by week:
    volume 01 = week of Jan 1  (may be a short partial week)
    volume 52 = the last week
    volume 53 = only in years where Dec 31 lands in a 53rd ISO week

Each weekly volume keeps the annual cover as its own cover (re-titled with
the week range) so every volume is a self-contained toilet book.

Output: ponderables/pdf/volumes/YYYY/SeymourWins_YYYY_weekNN.pdf

Run:  python3 split_weeks.py            (all years 2020-2026)
      python3 split_weeks.py 2020       (one year)
"""
import os, sys, datetime, shutil
import fitz  # pymupdf

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
ANNUAL = "seymour_wins_{y}_multiverse.pdf"
PAGES_PER_DAY = 31

def iso_week_of(year, month, day):
    return datetime.date(year, month, day).isocalendar()

def build_week_map(year):
    """Return list of (week_index_1based, [(month,day), ...]) for the year."""
    # find Dec 31 week number
    d = datetime.date(year, 12, 31)
    last_week = d.isocalendar()[1]
    # handle ISO years where week 1 of next year starts in this year's Dec
    # (e.g. 2020-12-31 is ISO week 53). We bucket by (isoyear, isoweek).
    weeks = {}
    for mm in range(1, 13):
        for dd in range(1, 32):
            try:
                dt = datetime.date(year, mm, dd)
            except ValueError:
                continue
            iso = dt.isocalendar()  # (isoyear, isoweek, weekday)
            # bucket key: isoweek within THIS calendar year's span
            key = iso[1]
            weeks.setdefault(key, []).append((mm, dd))
    # sort bucket keys; if any day maps to isoyear != year (rare edge), keep by isoweek
    keys = sorted(weeks.keys())
    return [(k, sorted(weeks[k])) for k in keys]

def split_year(year):
    src = os.path.join(BASE, ANNUAL.format(y=year))
    if not os.path.exists(src):
        print(f"  [skip] {src} not found"); return 0
    day_pages = []
    d = datetime.date(year, 1, 1)
    # map every calendar day -> its day-of-year index 0..365
    for n in range(366):
        try:
            dt = datetime.date(year, 1, 1) + datetime.timedelta(days=n)
        except ValueError:
            break
        day_pages.append(dt)

    wk = build_week_map(year)
    out_dir = os.path.join(BASE, "volumes", str(year))
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(src)
    n_weeks = 0
    for wi, (isowk, days) in enumerate(wk, start=1):
        # page range: cover (0) + each day's 31 pages, inserted as day-blocks
        out = os.path.join(out_dir, f"SeymourWins_{year}_week{wi:02d}.pdf")
        new = fitz.open()
        new.insert_pdf(doc, from_page=0, to_page=0)  # cover
        for mm, dd in days:
            dt = datetime.date(year, mm, dd)
            doy = (dt - datetime.date(year, 1, 1)).days
            start = 1 + doy * PAGES_PER_DAY
            new.insert_pdf(doc, from_page=start, to_page=start + PAGES_PER_DAY - 1)
        new.save(out)  # fast save; volumes are small (~3MB)
        new.close()
        n_weeks += 1
    doc.close()
    print(f"  {year}: {n_weeks} weekly volumes -> {out_dir}")
    return n_weeks

def main():
    years = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(2020, 2027))
    total = 0
    for y in years:
        print(f"splitting {y} ...", flush=True)
        total += split_year(y)
    print(f"WEEKLY SPLIT COMPLETE: {total} volumes across {len(years)} years")

if __name__ == "__main__":
    main()
