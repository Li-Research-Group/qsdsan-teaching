'''
Precompute a (SRT, S_0) grid of ActivatedSludgeProcess results using the
real QSDsan simulation, for the standalone HTML SRT/HRT module
(html/srt_hrt.html).

Every number in the grid comes from an actual `qsdsan_teaching.systems
.simulate_asp` call -- QSDsan is still what computes the physics, this
script just runs it once, offline, across a grid instead of once per
slider move in a browser.

Grid design notes (see tests/test_systems.py for the checks backing these):
- SRT is swept as whole days only (0..25). ActivatedSludgeProcess rounds
  SRT to the nearest whole day internally, so finer sampling would just
  repeat the same results. SRT starts at 0 (not 1) so the washed-out
  region (SRT <= SRT_min, which this module's default kinetics put at
  2.5 d -- see `DEFAULT_KINETICS` in `qsdsan_teaching/systems.py`) is
  actually visible as a region of the grid, not just a single edge value.
- S_0 (influent strength) does need a real 2-D sweep: effluent COD is
  NOT exactly independent of S_0 in this unit's actual output (only the
  underlying textbook substrate-concentration formula is; the unit then
  apportions that value across the influent's Substrate fraction, which
  does shift with S_0). SRT still dominates, but the dependence is real.
- Q (influent flow) needs no grid at all: WAS production and reactor
  volume both scale exactly linearly with Q at fixed (SRT, S_0), so only
  one reference Q is precomputed and the page scales them by Q/Q_ref
  client-side.

Usage: python scripts/precompute_asp_grid.py
Writes the grid into html/srt_hrt.html in place (replacing the contents
of the `id="asp-grid-data"` script tag), so the page stays a single
self-contained file that works fully offline.
'''

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qsdsan_teaching.systems import simulate_asp

SRT_GRID = list(range(0, 26))        # 0..25 d (0 = washed-out marker)
S0_GRID = list(range(100, 601, 25))  # 100..600 mg/L, step 25
Q_REF = 20  # MGD; WAS_rate scales exactly linearly with Q from this reference

HTML_PATH = Path(__file__).resolve().parent.parent / 'html' / 'srt_hrt.html'
DATA_TAG_RE = re.compile(
    r'(<script id="asp-grid-data" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)


def build_grid():
    SRT_min = None
    effluent_COD, HRT_hr, WAS_rate_at_Qref, V_reactor_at_Qref = [], [], [], []

    for srt in SRT_GRID:
        cod_row, hrt_row, was_row, v_row = [], [], [], []
        for s0 in S0_GRID:
            result = simulate_asp(Q=Q_REF, S_0=s0, SRT=srt)
            if SRT_min is None:
                SRT_min = result['SRT_min']
            if result['washed_out']:
                cod_row.append(None)
                hrt_row.append(None)
                was_row.append(None)
                v_row.append(None)
            else:
                cod_row.append(round(result['effluent_COD'], 4))
                hrt_row.append(round(result['HRT'], 4))
                was_row.append(round(result['WAS_rate'], 4))
                v_row.append(round(result['V_reactor'], 4))
        effluent_COD.append(cod_row)
        HRT_hr.append(hrt_row)
        WAS_rate_at_Qref.append(was_row)
        V_reactor_at_Qref.append(v_row)
        print(f'  SRT={srt:>2} d done')

    return {
        'SRT_grid': SRT_GRID,
        'S0_grid': S0_GRID,
        'Q_ref': Q_REF,
        'SRT_min': round(SRT_min, 4),
        'effluent_COD': effluent_COD,          # [SRT_idx][S0_idx] -> mg/L, or null if washed out
        'HRT_hr': HRT_hr,                      # [SRT_idx][S0_idx] -> hr
        'WAS_rate_at_Qref': WAS_rate_at_Qref,   # [SRT_idx][S0_idx] -> kg/d at Q=Q_ref
        'V_reactor_at_Qref': V_reactor_at_Qref, # [SRT_idx][S0_idx] -> m3 at Q=Q_ref
    }


def main():
    print(f'Precomputing {len(SRT_GRID)} x {len(S0_GRID)} grid '
          f'({len(SRT_GRID) * len(S0_GRID)} simulate_asp calls)...')
    grid = build_grid()

    html = HTML_PATH.read_text(encoding='utf-8')
    new_data_block = json.dumps(grid)
    html, n = DATA_TAG_RE.subn(
        lambda m: m.group(1) + new_data_block + m.group(3), html, count=1)
    if n != 1:
        raise RuntimeError(
            f'Could not find the asp-grid-data script tag in {HTML_PATH}')
    HTML_PATH.write_text(html, encoding='utf-8')
    print(f'Wrote grid into {HTML_PATH}')


if __name__ == '__main__':
    main()
