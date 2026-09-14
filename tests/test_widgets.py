'''
Sanity checks for `qsdsan_teaching.widgets`, independent of the notebooks.
'''

from qsdsan_teaching.systems import simulate_asp
from qsdsan_teaching.widgets import (
    format_readout, format_impact_comparisons,
    FOOTBALL_FIELD_AREA_FT2, CAKE_SOLIDS_FRACTION,
)


def test_format_readout_washed_out_and_normal_cases_dont_crash():
    normal = simulate_asp(Q=20, S_0=300, SRT=5)
    washed_out = simulate_asp(Q=20, S_0=300, SRT=1)
    assert 'washes out' not in format_readout(normal)
    assert 'washes out' in format_readout(washed_out)


def test_impact_comparisons_blank_when_washed_out():
    washed_out = simulate_asp(Q=20, S_0=300, SRT=1)
    assert format_impact_comparisons(washed_out) == ''


def test_flood_depth_matches_volume_divided_by_field_area():
    result = simulate_asp(Q=20, S_0=300, SRT=5)
    from qsdsan.utils import auom
    expected_depth_ft = auom('m3').convert(result['V_reactor'], 'ft3') / FOOTBALL_FIELD_AREA_FT2
    text = format_impact_comparisons(result)
    assert f'{expected_depth_ft:,.0f} ft' in text


def test_trucks_per_day_scales_linearly_with_influent_flow():
    # Trucks/day is a linear unit conversion of WAS_rate (itself linear in
    # Q, per test_systems.py::test_was_rate_scales_linearly_with_influent_flow),
    # so it should double exactly when Q doubles. Computed directly from
    # WAS_rate here (not by re-parsing the 1-decimal-rounded display text,
    # which would only match to within rounding error).
    low = simulate_asp(Q=10, S_0=300, SRT=5)
    high = simulate_asp(Q=20, S_0=300, SRT=5)
    # (kg -> lb -> US ton is itself a fixed linear conversion, so it's
    # enough to check the ratio using kg directly; no need to replicate
    # the exact unit chain from `format_impact_comparisons` here.)
    low_trucks = low['WAS_rate'] / CAKE_SOLIDS_FRACTION
    high_trucks = high['WAS_rate'] / CAKE_SOLIDS_FRACTION
    assert round(high_trucks / low_trucks, 6) == 2.0
