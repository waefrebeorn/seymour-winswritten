# SEYMOUR WINS — CALENDAR ARCHITECTURE

## The publication model (NEW — supersedes old Volume model for "Seymour Wins")

Seymour Wins is a **daily memetic journal** in toilet-book form.

| Unit | Span | Pages | Build input |
|------|------|------:|-------------|
| **Issue** | 1 day | 1 page | `calendar/YYYY/MM/DD.md` (one daily entry) |
| **Volume** | 1 month | ~28–31 pp | all issues in `calendar/YYYY/MM/` + cover |
| **Annual** | 1 year | ~365 pp | all 12 monthly volumes, bound as one book |
| **Through the Years** | N years | N×365 pp | same calendar date, every year, side by side |

### Format equation (verified, page = 4.5"×7.125", content area 6.875" = 495pt)
- One issue per page. Clipart 72px framed + captioned. Body 9pt, footnotes 7pt.
- `page-break-inside: avoid` per entry → no spill pages.
- Engine: `build_calendar.py` → HTML → Chromium `--print-to-pdf`.

---

## The memetic overlap-time system

The spine of the whole project. Every calendar date is a **thread** that runs
vertically through the years:

```
Jan 20  │ 2020: Wuhan lockdown            ┐
        │ 2021: Biden inauguration        │  SAME DATE,
        │ 2022: ...                       │  different year,
        │ 2023: ...                       ┘  memetic echo

"through the years" look = reading one date's column top to bottom.
"year by year" look     = reading one year's row left to right.
```

### How a daily issue is written (memetic system)
Each `DD.md` has:
- **REAL-WORLD FACT** — a verified anchor event for that date (backdated truth).
- **PONDERABLE** — Seymour's memetic lens on it (absurdist + genuinely insightful).
- **OVERLAP** — a `[[YYYY-MM-DD]]` link to another year's same-or-adjacent date,
  creating the cross-year echo. The engine resolves these into a "Through the
  Years" appendix per date.
- **CLIPART** — `theme: <dir>` resolved from `assets/clipart/<theme>/`.

### Why "COVID Cambrian Explosion" for 2020
2020 is the start date. The metaphor: like the Cambrian explosion (life's
body-plan diversity exploded in ~20M years), 2020 exploded the *memetic*
diversity of the internet — everyone suddenly became a content organism,
mutating formats (TikTok, Zoom, toilet-paper panic-buying as a meme, etc.).
Backdating to 2020 lets the series run "through the years" from the explosion
forward, with real-world facts as the fossil record.

---

## Directory layout
```
ponderables/calendar/
  YYYY/
    MM/
      DD.md            # one issue
      _volume.md       # optional month foreword / intro
    _year.md           # year framing (e.g. 2020 = COVID Cambrian Explosion)
    _facts.md          # real-world fact anchors per date (curated, cited)
  index.json           # generated: date -> file, overlap links
```

## Build commands
- `python3 build_calendar.py 2020 01`  → `pdf/seymour_wins_2020_01_jan.pdf`
- `python3 build_calendar.py 2020`     → `pdf/seymour_wins_2020_annual.pdf`
- `python3 build_calendar.py 2020 01 20 --through-years` → single-date column across years

## License / assets
Same as Ponderables: CC0 clipart (Openclipart mirror), OFL fonts, real-world
facts marked with source year. No fabricated events — dates anchor to history.
