#!/usr/bin/env python3
"""
Seymour Wins — VOLUMES META MANIFEST
=====================================================================
Scans ponderables/pdf/volumes/ and writes a committable JSON index
chronicling every weekly volume by year / ISO week / date range / pages.
This is SOURCE metadata (not a PDF) so it goes on GitHub; the PDFs stay
local (they are the product we sell).

Run: python3 volumes_manifest.py
"""
import os, json, glob, datetime
import fitz

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf", "volumes")

def main():
    manifest = {"generated": datetime.date.today().isoformat(), "years": {}}
    for year in sorted(os.listdir(BASE)):
        yp = os.path.join(BASE, year)
        if not os.path.isdir(yp):
            continue
        vols = []
        for fp in sorted(glob.glob(os.path.join(yp, "*.pdf"))):
            name = os.path.basename(fp)
            # parse week number from filename
            wk = int(name.split("week")[1].split(".")[0])
            # date range: first and last day-of-year in this week
            doc = fitz.open(fp)
            pages = doc.page_count
            doc.close()
            # reconstruct date range from week map
            d0 = datetime.date(int(year), 1, 1)
            # find the monday of this ISO week
            # week 1 of ISO year: the week containing Jan 4
            jan4 = datetime.date(int(year), 1, 4)
            wk1_monday = jan4 - datetime.timedelta(days=jan4.weekday())
            monday = wk1_monday + datetime.timedelta(weeks=wk - 1)
            sunday = monday + datetime.timedelta(days=6)
            start = max(monday, d0)
            end = min(sunday, datetime.date(int(year), 12, 31))
            vols.append({
                "volume": name.replace(".pdf", ""),
                "week": wk,
                "range": f"{start.strftime('%b %d')} – {end.strftime('%b %d')}",
                "days": (end - start).days + 1,
                "pages": pages,
                "file": f"ponderables/pdf/volumes/{year}/{name}",
            })
        manifest["years"][year] = {
            "volumes": len(vols),
            "total_pages": sum(v["pages"] for v in vols),
            "weeks": vols,
        }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VOLUMES_MANIFEST.json")
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    total_vols = sum(y["volumes"] for y in manifest["years"].values())
    total_pages = sum(y["total_pages"] for y in manifest["years"].values())
    print(f"Wrote {out}: {total_vols} weekly volumes, {total_pages} pages across {len(manifest['years'])} years")

if __name__ == "__main__":
    main()
