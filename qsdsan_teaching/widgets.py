'''Shared ipywidgets helpers for the teaching notebooks.'''

import ipywidgets as widgets
from qsdsan.utils import auom


def labeled_slider(label, value, min, max, step, **kwargs):
    '''A FloatSlider that only updates on release (not mid-drag), so a
    module can afford to re-simulate/re-plot on every change.'''
    return widgets.FloatSlider(
        value=value, min=min, max=max, step=step, description=label,
        continuous_update=False, style={'description_width': 'initial'},
        layout=widgets.Layout(width='400px'),
        **kwargs,
    )


def format_readout(result):
    '''Render a `systems.simulate_asp` results dict as a short text block.'''
    if result['washed_out']:
        return (
            'System washes out at this SRT (no stable effluent quality).\n'
            f"SRT_min = {result['SRT_min']:.2f} d - raise the safety factor "
            'so SRT exceeds it.'
        )
    V_MG = auom('m3').convert(result['V_reactor'], 'gal') / 1e6
    return (
        f"SRT = {result['SRT']:.1f} d  (SRT_min = {result['SRT_min']:.2f} d)\n"
        f"HRT = {result['HRT']:.1f} hr\n"
        f"Tank volume = {result['V_reactor']:,.0f} m3 ({V_MG:.2f} MG)\n"
        f"Effluent COD = {result['effluent_COD']:.1f} mg/L\n"
        f"WAS production = {result['WAS_rate']:.1f} kg/d"
    )


# Standard American football field including end zones: 360 x 160 ft =
# 57,600 sq ft (true for any regulation field, including SHI Stadium's --
# not a stadium-specific figure, just the rule-book field size). Used only
# for the "how deep would this tank flood a field" comparison below.
FOOTBALL_FIELD_AREA_FT2 = 360 * 160

# Illustrative assumptions for the "how many truckloads" comparison --
# not simulated outputs. Cake solids ~15-25% is typical for belt-press/
# centrifuge dewatering of municipal WAS; ~20 US tons/load is a commonly
# cited biosolids-hauling truck payload. Both vary by technology/hauler,
# so these are stated explicitly in the rendered text rather than hidden.
CAKE_SOLIDS_FRACTION = 0.20
TRUCK_CAPACITY_TON = 20  # US (short) tons


def format_impact_comparisons(result):
    '''
    Render tank-volume and WAS-production results as more tangible
    comparisons. These are illustrative unit conversions of the simulated
    `V_reactor`/`WAS_rate`, using the stated assumption constants above --
    not additional QSDsan outputs.
    '''
    if result['washed_out']:
        return ''
    V_ft3 = auom('m3').convert(result['V_reactor'], 'ft3')
    flood_depth_ft = V_ft3 / FOOTBALL_FIELD_AREA_FT2

    wet_cake_kg_d = result['WAS_rate'] / CAKE_SOLIDS_FRACTION
    wet_cake_ton_d = auom('kg').convert(wet_cake_kg_d, 'lb') / 2000  # US ton = 2000 lb
    trucks_per_day = wet_cake_ton_d / TRUCK_CAPACITY_TON

    return (
        f"For scale: this tank could flood a football field (like SHI "
        f"Stadium's, {FOOTBALL_FIELD_AREA_FT2:,} sq ft) to a depth of "
        f"about {flood_depth_ft:,.0f} ft.\n"
        f"Dewatered sludge (assuming {CAKE_SOLIDS_FRACTION:.0%} solids "
        f"cake, {TRUCK_CAPACITY_TON}-ton trucks) needs about "
        f"{trucks_per_day:.1f} truckloads/day."
    )
