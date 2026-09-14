'''Shared matplotlib helpers for the teaching notebooks.'''

_CURVE_COLOR = '#1f77b4'
_POINT_COLOR = '#d62728'
_THRESHOLD_COLOR = '#7f7f7f'
_PERMIT_COLOR = '#2ca02c'

# EPA's secondary treatment standard (40 CFR Part 133): 30 mg/L BOD5,
# 30-day average. This module's output is effluent COD, not BOD5 -- COD
# is typically higher than BOD5 for the same sample -- so this line is an
# approximate reference for scale, not an exact compliance threshold.
TYPICAL_BOD_PERMIT_LIMIT = 30  # mg/L BOD5


def plot_srt_curve(ax, SRT_values, COD_values, SRT_min, current_SRT,
                    current_COD, washed_out, title='Effect of SRT on effluent quality'):
    '''
    Plot effluent COD vs. SRT, with a vertical line at the washout
    threshold (`SRT_min`), a horizontal line at a typical BOD permit
    limit (for scale, not an exact compliance check -- see
    `TYPICAL_BOD_PERMIT_LIMIT`), and a marker at the student's current
    operating point.
    '''
    ax.clear()
    # marker='o': the unit rounds SRT to the nearest whole day internally,
    # so this is genuinely a sequence of discrete daily points, not a
    # continuous curve -- markers make that honest rather than implying
    # finer resolution than the model has.
    ax.plot(SRT_values, COD_values, '-o', color=_CURVE_COLOR, markersize=4,
             label='Effluent COD vs SRT')
    ax.axvline(SRT_min, color=_THRESHOLD_COLOR, linestyle='--',
               label=f'SRT_min = {SRT_min:.2f} d (washout)')
    ax.axhline(TYPICAL_BOD_PERMIT_LIMIT, color=_PERMIT_COLOR, linestyle=':',
               label=f'Typical permit limit ({TYPICAL_BOD_PERMIT_LIMIT} mg/L BOD5*)')
    if not washed_out:
        ax.plot(current_SRT, current_COD, 'o', color=_POINT_COLOR,
                 markersize=10, label='Current operating point')
    ax.set_xlabel('SRT (d)')
    ax.set_ylabel('Effluent COD (mg/L)')
    ax.set_title(title)
    ax.legend(loc='upper right', fontsize=8)
    ax.annotate('*BOD5 permit limit shown against modeled COD for scale only — not an exact compliance check',
                xy=(0, 0), xycoords='axes fraction', xytext=(0, -32),
                textcoords='offset points', fontsize=7, color='#888')
    return ax
