# qsdsan-teaching: SRT/HRT interactive teaching module

Date: 2026-09-14

## Purpose

Yalin Li (Rutgers CEE, Li Research Group) wants an interactive tool for
teaching water/wastewater treatment concepts, built on top of QSDsan. The
first concept: how changing solids retention time (SRT) and hydraulic
retention time (HRT) affects effluent quality in an activated sludge
process. Audience is her own students, used both as an in-class demo and
as homework. This repo is designed as the start of a small suite of such
modules, not a one-off.

## Non-goals (v1)

- No dynamic (ODE-based) ASM1/ASM2d simulation — steady-state only.
- No hosted web app / FastAPI backend — a local/Colab-runnable Jupyter
  notebook is sufficient for this audience.
- No attempt to expose every kinetic parameter in the UI — only the ones
  that serve the SRT/HRT teaching point.
- No authentication, deployment, or multi-user infrastructure.

## Architecture

Standalone git repo `Li-Research-Group/qsdsan-teaching`, structured as a
small reusable package plus one notebook per concept, so future modules
(nutrient removal, aeration/DO control, digester loading, etc.) can be
added as a new `systems.py` function + a new notebook, reusing shared
widget/plot helpers.

```
qsdsan-teaching/
  README.md
  environment.yml
  qsdsan_teaching/
    __init__.py
    systems.py     # one function per module: builds/returns a parameterized QSDsan System
    widgets.py      # shared ipywidgets helpers (labeled sliders, live-readout formatting)
    plotting.py      # shared matplotlib helpers (consistent style across modules)
  notebooks/
    01_srt_hrt_effluent_quality.ipynb
  tests/
    test_systems.py  # sanity-checks systems.py against known reference values
```

## Module 1: SRT/HRT -> effluent quality

Built on QSDsan's `ActivatedSludgeProcess`
(`qsdsan.unit_operations.static.ActivatedSludgeProcess`), a steady-state
Rittmann & McCarty textbook-kinetics model. A single simulation runs in
~0.2s, fast enough for real-time slider interaction with no ODE solver.

### `systems.py`: `build_asp_system(...)`

A function that takes the teaching-relevant parameters and returns a
built (but not yet simulated) QSDsan `System` wrapping one
`ActivatedSludgeProcess` unit, plus a `simulate_asp(...)` convenience
wrapper that runs it and returns a results `dict` with keys `SRT`,
`HRT`, `effluent_COD`, `WAS_rate`, and `washed_out` (bool). Wraps
QSDsan's own exceptions from
non-convergent/washed-out conditions into a clear "system washes out at
this SRT" condition the notebook layer can display without a traceback.

Parameters exposed: `SF` (safety factor on minimum SRT), influent flow
`Q`, influent substrate concentration. Kinetic parameters (`Y`, `q_hat`,
`K`, `b`, `f_d`) stay at literature defaults for v1 — not exposed as
sliders, to keep the first module focused.

### Notebook: `01_srt_hrt_effluent_quality.ipynb`

Centerpiece visualization: a curve of effluent COD vs. SRT (sweeping SF
across a range, other inputs held fixed at the current slider values),
with:
- a marker at the student's current operating point (current SF/SRT),
- a vertical dashed line at the theoretical `SRT_min` (washout
  threshold),
so students can see effluent COD spike as SRT approaches `SRT_min` —
this is the primary pedagogical payoff of the module.

Sliders built with `ipywidgets.interactive_output`, laid out explicitly
(sliders in a column beside the plot output) rather than the default
`interact` stacking, so the plot and live readouts stay pinned together:
`SF`, influent flow `Q`, influent substrate concentration.

Live readouts below/beside the plot: computed SRT (days), HRT (hours),
effluent COD (mg/L), WAS production rate.

### Error handling

Near `SF` close to 1 (SRT close to `SRT_min`) the underlying system can
fail to converge or produce a nonphysical/washed-out solution. `systems.py`
catches this and returns a "washed out" result state; the notebook
displays a clear message ("system washes out at this SRT — no stable
effluent quality") instead of letting a QSDsan/BioSTEAM traceback surface.

### Testing

`tests/test_systems.py` is a plain pytest file (not tied to the
notebook) that calls `build_asp_system`/`simulate_asp` with the same
inputs as QSDsan's own `ActivatedSludgeProcess` docstring example and
asserts effluent COD matches the documented reference value (19.0 mg/L),
guarding against upstream QSDsan changes silently breaking the teaching
module.

## Setup / sharing

`environment.yml` pins `qsdsan`, `jupyter`, `ipywidgets`, `matplotlib`.
README documents `conda env create` + `jupyter notebook` as the expected
student/TA workflow. Hosted/Binder/Colab deployment is an explicit
future option, not in v1 scope.

## Deviations from this spec made during implementation (2026-09-14)

Two changes were made while building module 1, both verified against the
real `qsdsan` install (v1.6.0) rather than assumed:

- **Primary slider is `SRT` (days), not `SF`.** Sweeping `SF` directly
  turned out to be a poor teaching control: `ActivatedSludgeProcess`
  internally rounds SRT to the nearest whole day, and with the docstring
  example's default kinetics `SRT_min` is tiny (~0.18 d), so most of a
  1-16 `SF` sweep collapsed onto the same 1-2 rounded SRT values.
  `systems.py`'s `build_asp_system`/`simulate_asp`/`effluent_cod_curve`
  now take `SRT` directly and derive the `SF` the unit needs internally
  (`SF = SRT / SRT_min`, computed from the unit's own `Y`/`q_hat`/`b`
  after construction, so no kinetics defaults are duplicated). This is a
  strictly better fit for the stated purpose (teaching how *SRT* affects
  effluent quality) and doesn't change the architecture, file layout, or
  any other part of the design.
- **`requirements.txt` + `venv`, not `environment.yml`/conda.** This
  machine has no conda available, and the existing QSDsan-platform
  checkout is itself set up with a plain `.venv`, not conda. Followed
  that precedent instead.

`simulate_asp`'s results dict also carries an additional `SRT_min` key
(not in the original spec's key list) — needed to draw the washout
threshold line on the plot and to word the washed-out message.

## Second round: standalone HTML export (2026-09-14, same day)

Voila (proposed as the "live app" delivery option, see below) proved
unreliable in practice (got stuck mid-execution for an extended time on
one run) and needs a running local process the whole time it's open.
Added a second delivery format instead: `scripts/precompute_asp_grid.py`
runs the real QSDsan simulation across a grid, offline, and embeds the
result as JSON into `html/srt_hrt.html` -- a single dependency-free file
with hand-rolled SVG plotting and vanilla JS (no CDN libraries, works
fully offline via `file://`, verified end-to-end with a headless Edge
render matching the Python reference values exactly).

Two corrections came out of building this:

- **Effluent COD is NOT exactly independent of influent strength (`S_0`)
  in the unit's actual output**, contrary to an earlier claim in this
  project (both in chat and in an initial notebook discussion prompt).
  The pure Rittmann & McCarty textbook formula for effluent substrate
  concentration *is* S_0-independent, but `ActivatedSludgeProcess` then
  apportions that value across the influent's "Substrate" component in
  proportion to `Substrate / (Substrate + X + X_inert)` -- so holding
  `X`/`X_inert` fixed while sweeping `S_0` does shift effluent COD by a
  real, if modest, amount (confirmed by inspecting
  `outs[0].iconc['Substrate']` directly, and pinned by
  `tests/test_systems.py::test_effluent_cod_depends_much_more_on_srt_than_on_influent_strength`).
  This is why the HTML export grids over both `SRT` and `S_0` rather than
  the originally-planned 1-D `SRT`-only sweep with S_0 handled by exact
  linear scaling. Only `Q` turned out to be exactly, linearly scalable
  (confirmed by `test_was_rate_scales_linearly_with_influent_flow`) and
  was left out of the grid.
- **SRT is a genuine step function, not smooth.** `ActivatedSludgeProcess`
  rounds `SRT` to the nearest whole day internally, so fractional target
  SRTs collapse onto the same integer result (e.g. requesting SRT=0.7 and
  SRT=1.3 both actually simulate at SRT=1). Both the notebook's slider
  (previously `step=0.1`) and the HTML export's grid were changed to
  whole-day resolution to match, and both plots now draw markers at each
  point rather than implying continuous resolution. The notebook's SRT
  slider minimum was also changed to 0 (not 1): since `SRT_min` (~0.18 d
  by default) always rounds to 0, SRT=0 is the only slider value that can
  actually demonstrate the washed-out state -- an earlier edit that moved
  the slider minimum to 1 (to "match integer resolution") accidentally
  made the washout demonstration unreachable, caught before shipping.

## Third round: tank volume output, and a friendlier SRT_min (2026-09-14)

Two more changes, both same day:

- **Added `V_reactor` (tank volume) as an output**, alongside the
  already-present `HRT` and `WAS_rate`. Computed as `Q * HRT` (the same
  reactor volume `ActivatedSludgeProcess._run` uses internally for its
  own mass-balance calculations, not re-derived), in m3, with the
  readout also showing an MG (million-US-gallon) conversion. Confirmed
  exactly linear in `Q` (like `WAS_rate`), so like `WAS_rate` it's
  precomputed once at `Q_ref` and scaled client-side in the HTML export
  rather than gridded.
- **Module now uses its own `DEFAULT_KINETICS`, not QSDsan's raw class
  defaults, so `SRT_min` = 2.5 d instead of ~0.18 d.** At the original
  defaults, `SRT_min` always rounds to 0 (SRT is whole-day-only, see
  above), so the washed-out state was reachable only at the single
  slider value SRT=0 -- a real teaching limitation, since it reads as an
  edge case rather than a visible region of the curve. `Y=0.5, q_hat=1.0,
  K=20, b=0.1` (vs. the class defaults' `q_hat=12, b=0.396`) gives
  `SRT_min=2.5` exactly, making SRT=0,1,2 all clearly washed out and
  SRT=3+ a dramatic recovery (COD ~101 mg/L at SRT=3 down to ~20 mg/L by
  SRT=20). These are within literature-plausible ranges for a lower-
  rate/extended-aeration-type process, not a specific textbook worked
  example -- worth knowing if this module is ever discussed as literally
  modeling generic BOD-heterotroph kinetics, since `SRT_min` this size is
  more typical of nitrification kinetics than generic BOD removal.
  `qsdsan_teaching/systems.py`'s `DEFAULT_KINETICS` docstring comment has
  the full reasoning. `tests/test_systems.py::test_reference_case_matches_qsdsan_docstring`
  now passes QSDsan's original class-default kinetics explicitly, so it
  keeps validating the wrapper against QSDsan's own documented example
  independent of this module's own default choice.

## Fourth round: permit reference line and tangible-scale comparisons (2026-09-14)

- **Horizontal permit-limit line** on the COD-vs-SRT plot (both formats):
  30 mg/L, EPA's secondary treatment standard (40 CFR Part 133, 30-day
  average BOD5). The model outputs COD, not BOD5, and COD is typically
  higher than BOD5 for the same sample, so this is labeled and footnoted
  as an approximate reference for scale, not an exact compliance check --
  `qsdsan_teaching/plotting.py`'s `TYPICAL_BOD_PERMIT_LIMIT`.
- **Tangible-scale comparisons** for `V_reactor` and `WAS_rate`, added as
  `qsdsan_teaching/widgets.py`'s `format_impact_comparisons` (Python) and
  mirrored in `html/srt_hrt.html`'s JS: tank volume shown as the depth it
  would flood a regulation football field (same dimensions as SHI
  Stadium's -- not a stadium-specific figure, field size is standardized
  by rule), and WAS production shown as dewatered-sludge truckloads/day,
  assuming 20% cake solids and 20-ton trucks. Both are explicit,
  stated-in-the-UI illustrative assumptions layered on top of the real
  simulated `V_reactor`/`WAS_rate` values, not additional QSDsan outputs
  -- kept in a visually distinct "for scale" box so they read as
  illustrative rather than as more simulation results.

## Fifth round: graphical impact comparisons, HTML explorer only (2026-09-14)

Replaced the text-only impact comparisons in `html/srt_hrt.html` (not the
notebook -- scoped to just the standalone page, per how the request was
worded) with hand-rolled SVG graphics:

- **Stadium cross-section fill.** A stylized bowl shape (illustrative, not
  a literal rendering of SHI Stadium's architecture) fills with water to
  the computed flood depth, on a fixed 0-150 ft visual scale so the
  picture stays legible and comparable across the slider range (real
  depth ranges from <1 ft to 600+ ft across the sliders' full range, a
  ~1000x span that an auto-scaled axis would have hidden by always
  looking "about as full"). Above 150 ft the water fills the frame and an
  explicit "overflowing the stadium!" label + wavy overflow line appears,
  rather than silently clipping. A ~30 ft regulation goalpost is drawn at
  the same fixed scale as a built-in size reference (real, fixed height;
  not stadium-specific either).
- **Truck grid.** One truck icon per truckload/day (whole trucks at full
  opacity, a fractional remainder shown as one reduced-opacity icon),
  wrapped into rows, with a text fallback ("+N more") past 40 icons for
  extreme slider settings (observed max in practice: ~18/day).

Both were verified by actually rendering the page in a headless browser
and looking at the screenshot (`msedge --headless=new --disable-gpu
--screenshot=<absolute path>` -- a relative output path silently fails
with "Access is denied"; must use an absolute path), across three states
(default, an extreme overflow case, and washed-out), not just by
confirming the SVG-generating code runs without a JS error.
