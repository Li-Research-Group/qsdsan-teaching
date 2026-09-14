'''
Sanity checks for `qsdsan_teaching.systems`, independent of the notebooks.
'''

from qsdsan_teaching.systems import simulate_asp, effluent_cod_curve


def test_reference_case_matches_qsdsan_docstring():
    # Passes QSDsan's own ActivatedSludgeProcess class defaults explicitly
    # (this module's DEFAULT_KINETICS differ -- see that constant's
    # comment), to check the wrapper against QSDsan's own documented
    # example independent of this module's own default choice. SF=4 in
    # that docstring example rounds to the same SRT=1 d as requesting
    # SRT=1 directly.
    result = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=1,
                            Y=0.5, q_hat=12, K=20, b=0.396)
    assert not result['washed_out']
    assert result['SRT'] == 1
    assert round(result['effluent_COD'], 1) == 19.0


def test_low_srt_washes_out():
    result = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=0.05)
    assert result['washed_out']
    assert result['effluent_COD'] != result['effluent_COD']  # NaN


def test_srt_min_matches_kinetics_formula():
    Y, q_hat, b = 0.5, 12, 0.396
    result = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=5,
                            Y=Y, q_hat=q_hat, b=b)
    expected_srt_min = 1 / (Y * q_hat - b)
    assert result['SRT_min'] == expected_srt_min


def test_default_kinetics_give_a_clearly_nonzero_washout_threshold():
    # This module's DEFAULT_KINETICS (see systems.py) are deliberately
    # chosen so SRT_min lands well above 0 once rounded to a whole day
    # (QSDsan's own class defaults give SRT_min ~0.18 d, which rounds to
    # 0 -- washout would only be reachable at the single slider value
    # SRT=0, not as a visible region of the curve).
    result = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=5)
    assert result['SRT_min'] == 2.5
    assert not simulate_asp(Q=20, S_0=300, SRT=3)['washed_out']
    assert simulate_asp(Q=20, S_0=300, SRT=2)['washed_out']


def test_effluent_cod_curve_skips_washed_out_points_and_is_monotonic():
    SRT_values = [1, 2, 3, 4, 6, 10, 16, 22]
    actual_SRT_values, COD_values = effluent_cod_curve(
        SRT_values, Q=20, S_0=300, X=50, X_inert=100)
    # SRT <= SRT_min (2.5 d) should be excluded (washed out)
    assert len(actual_SRT_values) == len(COD_values) == 6
    # Effluent COD should fall (or hold) as SRT rises
    assert COD_values == sorted(COD_values, reverse=True)


def test_effluent_cod_depends_much_more_on_srt_than_on_influent_strength():
    # Rittmann & McCarty's textbook result is that effluent *substrate*
    # concentration at steady state is a function of SRT and kinetics only.
    # ActivatedSludgeProcess computes that theoretical S from kinetics alone,
    # but then apportions it across the influent's "Substrate" component in
    # proportion to (Substrate) / (Substrate + X + X_inert) -- i.e. relative
    # to the *other*, fixed influent components -- so effluent COD is NOT
    # exactly S_0-independent in this unit's actual output (confirmed by
    # inspecting `outs[0].iconc['Substrate']` directly: it does vary with
    # S_0 even at fixed X/X_inert). This is why the HTML export grids over
    # both SRT and S_0 rather than assuming a 1-D SRT-only curve. What does
    # hold, and is checked here: SRT still dominates.
    low_srt = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=3)['effluent_COD']
    high_srt = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=20)['effluent_COD']
    srt_driven_change = abs(low_srt - high_srt)

    low_s0 = simulate_asp(Q=20, S_0=100, X=50, X_inert=100, SRT=5)['effluent_COD']
    high_s0 = simulate_asp(Q=20, S_0=600, X=50, X_inert=100, SRT=5)['effluent_COD']
    s0_driven_change = abs(low_s0 - high_s0)

    assert s0_driven_change > 0  # real, not exactly zero
    assert srt_driven_change > 3 * s0_driven_change  # but SRT dominates


def test_was_rate_scales_linearly_with_influent_flow():
    # WAS production is an extensive (mass/time) quantity that should scale
    # exactly with Q at fixed SRT/S_0 (HRT and reactor sizing are intensive
    # and don't depend on Q). This is what lets the HTML export scale a
    # single precomputed WAS_rate by Q/Q_ref instead of gridding over Q.
    low = simulate_asp(Q=10, S_0=300, X=50, X_inert=100, SRT=5)
    high = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=5)
    assert high['HRT'] == low['HRT']  # intensive, Q-independent
    assert round(high['WAS_rate'] / low['WAS_rate'], 6) == 2.0


def test_reactor_volume_scales_linearly_with_influent_flow():
    # V_reactor (= Q * HRT) is extensive like WAS_rate: since HRT is
    # Q-independent (see test above), V_reactor should scale exactly
    # linearly with Q. This is what lets the HTML export scale a single
    # precomputed V_reactor by Q/Q_ref instead of gridding over Q.
    low = simulate_asp(Q=10, S_0=300, X=50, X_inert=100, SRT=5)
    high = simulate_asp(Q=20, S_0=300, X=50, X_inert=100, SRT=5)
    assert low['V_reactor'] > 0
    assert round(high['V_reactor'] / low['V_reactor'], 6) == 2.0
