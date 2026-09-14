# qsdsan-teaching

Interactive Jupyter notebooks for teaching water/wastewater treatment
concepts, built on [QSDsan](https://qsdsan.com). Each notebook is a
self-contained module; `qsdsan_teaching/` holds the reusable pieces
(system builders, widget helpers, plotting helpers) they share.

## Setup

```
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
jupyter lab
```

Then open a notebook under `notebooks/`.

## In-class demo / sharing with students (standalone HTML, recommended)

Each notebook has a matching precomputed, dependency-free HTML page under
`html/` that needs no Python, no server, and no install to view — open it
by double-clicking, email it, or host it as a static file (e.g. GitHub
Pages):

```
html/srt_hrt.html
```

The sliders still reflect real QSDsan `ActivatedSludgeProcess` output,
but computed *offline* ahead of time across a grid
(`scripts/precompute_asp_grid.py`) rather than live in the browser — see
the page's own footnote for exactly what's gridded vs. exactly scaled.
Regenerate it after changing the model or its default kinetics:

```
python scripts/precompute_asp_grid.py
```

## In-class demo, live simulation (Voilà)

To show a module as a clean, code-free *live* app instead of a static
page (sliders and plots only, no cells, with a real QSDsan simulation run
on every slider move) run:

```
voila notebooks/01_srt_hrt_effluent_quality.ipynb
```

Close the terminal running `voila` to stop it. In practice this has been
unreliable (a run got stuck mid-execution for an extended time on one
machine) and needs a running local process the whole time it's open —
prefer the static HTML page above unless you specifically need live
simulation.

## Modules

- [`01_srt_hrt_effluent_quality.ipynb`](notebooks/01_srt_hrt_effluent_quality.ipynb) /
  [`html/srt_hrt.html`](html/srt_hrt.html) —
  how solids retention time (SRT) affects effluent quality in an
  activated sludge process, and why real plants operate well above the
  theoretical minimum SRT.

## Adding a new module

1. Add a `build_<name>_system` / `simulate_<name>` pair to
   `qsdsan_teaching/systems.py`, returning a plain dict of results (not
   raw QSDsan objects) so the widget/plotting layer doesn't need to know
   about QSDsan internals. Before assuming a variable can be dropped from
   a static export's grid (e.g. because theory says the output shouldn't
   depend on it), verify that against the unit's actual numeric output —
   see the `SRT`/`S_0`/`Q` design notes in
   `scripts/precompute_asp_grid.py` for a case where the pure-kinetics
   theory and the unit's actual output disagreed by a small but real
   amount.
2. Add a `NN_<topic>.ipynb` notebook under `notebooks/` that wires up
   sliders (`qsdsan_teaching.widgets`) and a plot
   (`qsdsan_teaching.plotting`) around it.
3. Add a sanity-check test in `tests/test_systems.py` that pins at least
   one result against a known reference value, so an upstream QSDsan
   change that silently breaks the module gets caught by `pytest`
   instead of only showing up as a wrong-looking notebook plot.
4. Optionally add a `scripts/precompute_<name>_grid.py` (following
   `precompute_asp_grid.py`) and a matching `html/<name>.html` for a
   dependency-free, shareable version of the module.

## Testing

```
pytest
```
