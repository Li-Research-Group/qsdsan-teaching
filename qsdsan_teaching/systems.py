'''
Build and run a steady-state activated-sludge QSDsan system for the
SRT/HRT teaching module.

Effluent quality is governed by QSDsan's own `ActivatedSludgeProcess`
kinetics (Rittmann & McCarty steady-state model); this module doesn't
re-derive any of that math, it just wires up a System, runs it, and
reads back the results in a form the widgets/plotting layer can use.
'''

from itertools import count
from qsdsan import System, WasteStream, Stream
from qsdsan.utils import create_example_wwt_components
from qsdsan.unit_operations import ActivatedSludgeProcess

# Registers the example component set as the active thermo package.
# Done once at import time since it's global QSDsan state.
create_example_wwt_components()

# Widget-driven use rebuilds the system on every slider change; give each
# build unique unit/stream IDs so QSDsan's registry doesn't warn about
# reusing 'ASP', 'inf', etc. on every call.
_call_count = count()

# ActivatedSludgeProcess's own class defaults (Y=0.5, q_hat=12, b=0.396)
# give SRT_min ~= 0.18 d, which rounds to 0 in the unit's whole-day SRT
# resolution -- so on the module's integer-day SRT slider, "washed out"
# is only reachable at the single value SRT=0, not as a visible point on
# the curve. These defaults instead target SRT_min = 2.5 d (Y*q_hat - b =
# 0.4), a clearly nonzero, several-slider-steps-wide washout region,
# using kinetics within literature ranges for a lower-rate/extended-
# aeration-type process rather than a specific textbook worked example --
# see the design spec's addendum for the reasoning and the alternative
# considered (SRT_min this size is much more typical of nitrification
# kinetics than generic BOD-heterotroph kinetics, which is worth knowing
# if this module is ever discussed as literally modeling BOD removal
# kinetics rather than an illustrative SRT/washout demo).
DEFAULT_KINETICS = dict(Y=0.5, q_hat=1.0, K=20, b=0.1)


def build_asp_system(Q=20, S_0=300, X=50, X_inert=100, SRT=5, **kinetics):
    '''
    Build (but do not simulate) a one-unit QSDsan `System` around a
    steady-state `ActivatedSludgeProcess`.

    `ActivatedSludgeProcess` itself takes a safety factor `SF` (SRT =
    SRT_min * SF) rather than a target SRT directly, since SRT_min depends
    on the kinetics. For a teaching slider, "target SRT in days" is a much
    more direct concept than "safety factor", so this wrapper takes `SRT`
    and derives the `SF` the unit needs from the unit's own Y/q_hat/b
    (after construction, so no kinetics defaults are duplicated here).

    Parameters
    ----------
    Q : float
        Influent flow rate, [MGD].
    S_0 : float
        Influent soluble substrate (COD) concentration, [mg/L].
    X, X_inert : float
        Influent particulate active/inert biomass concentration, [mg/L].
    SRT : float
        Target solids retention time, [d]. The unit internally rounds this
        to the nearest whole day.
    kinetics : dict
        Additional `ActivatedSludgeProcess` kinetic parameters (e.g. `Y`,
        `q_hat`, `K`, `b`). Defaults to this module's own `DEFAULT_KINETICS`
        (not QSDsan's raw class defaults -- see that constant's docstring
        comment for why); pass e.g. `Y=0.5, q_hat=12, b=0.396` explicitly
        to reproduce QSDsan's own documented example instead.

    Returns
    -------
    qsdsan.System
    '''
    n = next(_call_count)
    inf = WasteStream(f'inf{n}')
    inf.set_flow_by_concentration(
        flow_tot=Q,
        concentrations={'Substrate': S_0, 'X': X, 'X_inert': X_inert},
        units=('mgd', 'mg/L'),
    )
    ASP = ActivatedSludgeProcess(
        f'ASP{n}', ins=(inf, Stream(f'air{n}')),
        outs=(f'treated{n}', f'was{n}', f'offgas{n}'),
        **{**DEFAULT_KINETICS, **kinetics},
    )
    SRT_min = 1 / (ASP.Y * ASP.q_hat - ASP.b)
    ASP.SF = SRT / SRT_min
    return System(f'sys{n}', path=(ASP,))


def simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=5, **kinetics):
    '''
    Build and simulate an activated-sludge system, returning a results
    dict rather than the raw QSDsan objects.

    Returns
    -------
    dict with keys:
        SRT, SRT_min : [d] actual (rounded) and washout-threshold solids
            retention time
        HRT : [hr] hydraulic retention time
        V_reactor : [m3] aeration tank volume (= Q * HRT, the same
            reactor volume the unit's own mass balance uses internally)
        effluent_COD : [mg/L]
        WAS_rate : [kg/d] waste-activated-sludge solids production rate
        washed_out : bool, True if requested SRT <= SRT_min (no stable
            effluent quality)

    When `washed_out` is True, the other numeric fields are `float('nan')`.
    '''
    sys = build_asp_system(Q=Q, S_0=S_0, X=X, X_inert=X_inert, SRT=SRT, **kinetics)
    ASP = sys.path[0]

    # Same formula as `ActivatedSludgeProcess._run` (SRT isn't saved on the
    # unit itself, only HRT is, so the actual rounded SRT it will use is
    # recomputed here from the same Y/q_hat/b/SF inputs it was just built
    # with).
    SRT_min = 1 / (ASP.Y * ASP.q_hat - ASP.b)
    SRT_actual = round(SRT_min * ASP.SF)

    nan = float('nan')
    if SRT <= SRT_min:
        return dict(SRT=SRT_actual, SRT_min=SRT_min, HRT=nan, V_reactor=nan,
                    effluent_COD=nan, WAS_rate=nan, washed_out=True)

    try:
        sys.simulate()
    except Exception:
        return dict(SRT=SRT_actual, SRT_min=SRT_min, HRT=nan, V_reactor=nan,
                    effluent_COD=nan, WAS_rate=nan, washed_out=True)

    was = ASP.outs[1]
    WAS_rate = was.get_TSS() * was.F_vol * 24 / 1000  # mg/L * m3/hr * hr/d / (mg/kg -> effectively /1000) = kg/d

    return dict(
        SRT=SRT_actual,
        SRT_min=SRT_min,
        HRT=ASP.HRT * 24,  # d -> hr
        V_reactor=ASP.Q * ASP.HRT,  # [m3/d] * [d] = m3
        effluent_COD=ASP.outs[0].COD,
        WAS_rate=WAS_rate,
        washed_out=False,
    )


def effluent_cod_curve(SRT_values, Q=20, S_0=300, X=50, X_inert=100, **kinetics):
    '''
    Run `simulate_asp` across a range of target SRTs and collect the
    (actual SRT, effluent_COD) pairs for plotting, skipping washed-out
    points.

    Parameters
    ----------
    SRT_values : Iterable[float]
        Target SRTs to sweep, [d].

    Returns
    -------
    (SRT_values, COD_values) : tuple[list[float], list[float]]
    '''
    actual_SRT_values, COD_values = [], []
    for SRT in SRT_values:
        result = simulate_asp(Q=Q, S_0=S_0, X=X, X_inert=X_inert, SRT=SRT, **kinetics)
        if not result['washed_out']:
            actual_SRT_values.append(result['SRT'])
            COD_values.append(result['effluent_COD'])
    return actual_SRT_values, COD_values
