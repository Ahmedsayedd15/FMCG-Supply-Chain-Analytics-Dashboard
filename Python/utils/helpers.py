"""
utils/helpers.py
=================
Shared helper functions: date ranges, seasonality multipliers, weighted
sampling utilities. Used by every generator to keep business logic (e.g.
Ramadan effects) consistent across phases instead of re-implemented per file.
"""

import numpy as np
import pandas as pd
from config import RAMADAN_RANGES, EID_AL_FITR, EID_AL_ADHA, RNG


def month_range(start, end):
    return pd.date_range(start=start, end=end, freq="MS")


def is_ramadan(date):
    d = pd.Timestamp(date)
    for s, e in RAMADAN_RANGES:
        if pd.Timestamp(s) <= d <= pd.Timestamp(e):
            return True
    return False


def is_near_eid(date, window_days=5):
    d = pd.Timestamp(date)
    for e in EID_AL_FITR + EID_AL_ADHA:
        if abs((d - pd.Timestamp(e)).days) <= window_days:
            return True
    return False


def is_summer(date):
    return pd.Timestamp(date).month in (6, 7, 8)


def is_back_to_school(date):
    return pd.Timestamp(date).month == 9


def seasonal_multiplier_for_month(month_start_date, category_row):
    """Combine category-specific seasonality effects for a given month."""
    mult = 1.0
    days_in_month = pd.Period(month_start_date, freq="M").days_in_month
    sample_days = [month_start_date + pd.Timedelta(days=d) for d in range(0, days_in_month, 5)]

    ramadan_days = sum(1 for d in sample_days if is_ramadan(d))
    eid_days = sum(1 for d in sample_days if is_near_eid(d))
    summer_days = sum(1 for d in sample_days if is_summer(d))

    frac_ramadan = ramadan_days / len(sample_days)
    frac_eid = eid_days / len(sample_days)
    frac_summer = summer_days / len(sample_days)

    mult *= (1 + frac_ramadan * (category_row["ramadan_mult"] - 1))
    mult *= (1 + frac_eid * (category_row["eid_mult"] - 1))
    mult *= (1 + frac_summer * (category_row["summer_mult"] - 1))

    if month_start_date.month == 9:
        mult *= 1.05  # mild back-to-school lift across categories

    # mild general noise so it's not perfectly deterministic per category
    mult *= RNG.normal(1.0, 0.03)
    return max(mult, 0.4)


def weighted_choice(rng, options, weights, size=1):
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()
    return rng.choice(options, size=size, p=weights)


def zipf_weights(n, s=1.1):
    ranks = np.arange(1, n + 1)
    w = 1.0 / np.power(ranks, s)
    return w / w.sum()


def random_dates_between(rng, start, end, n):
    start_ts = pd.Timestamp(start).value // 10**9
    end_ts = pd.Timestamp(end).value // 10**9
    rand_ts = rng.integers(start_ts, end_ts, size=n)
    return pd.to_datetime(rand_ts, unit="s")


def clip_series(s, lo, hi):
    return np.clip(s, lo, hi)
