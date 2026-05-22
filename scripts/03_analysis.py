"""
Trend analysis using Mann-Kendall test and Theil-Sen slope.

This script reproduces the central trend-analysis framework used by Qu et al. (2016):
    - Mann-Kendall test for monotonic trend significance
    - Theil-Sen slope estimate
    - slope converted to change per decade

Outputs:
    outputs/tables/city_summary_statistics.csv
    outputs/tables/city_mk_theilsen_trends.csv
    outputs/tables/city_intensity_composition.csv
"""

from __future__ import annotations

from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.stats import norm, theilslopes


ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "processed" / "city_annual_precip_intensity_indices.csv"
TABLE_DIR = ROOT / "outputs" / "tables"

SUMMARY_FILE = TABLE_DIR / "city_summary_statistics.csv"
TREND_FILE = TABLE_DIR / "city_mk_theilsen_trends.csv"
COMPOSITION_FILE = TABLE_DIR / "city_intensity_composition.csv"

CATEGORY_ORDER = ["light", "moderate", "heavy", "extreme"]
TREND_METRICS = [
    "annual_precip",
    "light_amount",
    "moderate_amount",
    "heavy_amount",
    "extreme_amount",
    "light_amount_ratio",
    "moderate_amount_ratio",
    "heavy_amount_ratio",
    "extreme_amount_ratio",
    "light_days",
    "moderate_days",
    "heavy_days",
    "extreme_days",
    "max_1day_precip",
]

METRIC_LABELS = {
    "annual_precip": "Annual precipitation",
    "light_amount": "Light precipitation amount",
    "moderate_amount": "Moderate precipitation amount",
    "heavy_amount": "Heavy precipitation amount",
    "extreme_amount": "Extreme precipitation amount",
    "light_amount_ratio": "Light precipitation proportion",
    "moderate_amount_ratio": "Moderate precipitation proportion",
    "heavy_amount_ratio": "Heavy precipitation proportion",
    "extreme_amount_ratio": "Extreme precipitation proportion",
    "light_days": "Light precipitation days",
    "moderate_days": "Moderate precipitation days",
    "heavy_days": "Heavy precipitation days",
    "extreme_days": "Extreme precipitation days",
    "max_1day_precip": "Annual maximum 1-day precipitation",
}


def mann_kendall_test(values: pd.Series) -> dict[str, float | str]:
    """Two-sided Mann-Kendall test with tie correction."""
    x = pd.Series(values).dropna().to_numpy(dtype=float)
    n = len(x)
    if n < 3:
        return {"mk_s": np.nan, "mk_z": np.nan, "mk_p": np.nan, "mk_trend": "insufficient"}

    s = 0
    for k in range(n - 1):
        s += int(np.sign(x[k + 1 :] - x[k]).sum())

    unique, counts = np.unique(x, return_counts=True)
    tie_sum = sum(c * (c - 1) * (2 * c + 5) for c in counts if c > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - tie_sum) / 18

    if var_s <= 0:
        z = 0.0
    elif s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0

    p_value = 2 * norm.sf(abs(z))
    if p_value < 0.05 and z > 0:
        trend = "increasing"
    elif p_value < 0.05 and z < 0:
        trend = "decreasing"
    else:
        trend = "no significant trend"

    return {"mk_s": s, "mk_z": z, "mk_p": p_value, "mk_trend": trend}


def significance_symbol(p_value: float) -> str:
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "+"
    return ""


def theil_sen_slope(years: pd.Series, values: pd.Series) -> dict[str, float]:
    clean = pd.DataFrame({"year": years, "value": values}).dropna()
    if clean.shape[0] < 3:
        return {
            "sen_slope_per_year": np.nan,
            "sen_slope_per_decade": np.nan,
            "sen_intercept": np.nan,
            "sen_low_slope": np.nan,
            "sen_high_slope": np.nan,
        }

    result = theilslopes(clean["value"].to_numpy(), clean["year"].to_numpy(), alpha=0.95)
    slope, intercept, low_slope, high_slope = result[0], result[1], result[2], result[3]
    return {
        "sen_slope_per_year": slope,
        "sen_slope_per_decade": slope * 10,
        "sen_intercept": intercept,
        "sen_low_slope": low_slope,
        "sen_high_slope": high_slope,
    }


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "annual_precip",
        "wet_days",
        "light_amount",
        "moderate_amount",
        "heavy_amount",
        "extreme_amount",
        "light_days",
        "moderate_days",
        "heavy_days",
        "extreme_days",
        "light_amount_ratio",
        "moderate_amount_ratio",
        "heavy_amount_ratio",
        "extreme_amount_ratio",
        "max_1day_precip",
    ]
    summary = df.groupby(["city", "city_cn", "province"], as_index=False)[metrics].mean()
    summary = summary.rename(columns={col: f"mean_{col}" for col in metrics})
    return summary.round(6)


def build_composition_table(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (city, city_cn, province), group in df.groupby(["city", "city_cn", "province"]):
        total = group["annual_precip"].sum()
        for cat in CATEGORY_ORDER:
            amount = group[f"{cat}_amount"].sum()
            days = group[f"{cat}_days"].sum()
            records.append(
                {
                    "city": city,
                    "city_cn": city_cn,
                    "province": province,
                    "category": cat,
                    "category_label": METRIC_LABELS[f"{cat}_amount"],
                    "total_amount": amount,
                    "total_days": days,
                    "amount_share": amount / total if total > 0 else np.nan,
                    "mean_annual_amount": group[f"{cat}_amount"].mean(),
                    "mean_annual_days": group[f"{cat}_days"].mean(),
                    "mean_annual_share": group[f"{cat}_amount_ratio"].mean(),
                }
            )
    return pd.DataFrame(records).round(6)


def build_trend_table(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (city, city_cn, province), group in df.groupby(["city", "city_cn", "province"]):
        for metric in TREND_METRICS:
            mk = mann_kendall_test(group[metric])
            sen = theil_sen_slope(group["year"], group[metric])
            records.append(
                {
                    "city": city,
                    "city_cn": city_cn,
                    "province": province,
                    "metric": metric,
                    "metric_label": METRIC_LABELS.get(metric, metric),
                    **mk,
                    **sen,
                    "significance": significance_symbol(mk["mk_p"]),
                }
            )

    trend_df = pd.DataFrame(records)
    return trend_df.round(8)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Annual intensity file not found: {INPUT_FILE}. Run scripts/02_preprocess.py first."
        )

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_FILE)

    summary = build_summary(df)
    composition = build_composition_table(df)
    trend = build_trend_table(df)

    summary.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")
    composition.to_csv(COMPOSITION_FILE, index=False, encoding="utf-8-sig")
    trend.to_csv(TREND_FILE, index=False, encoding="utf-8-sig")

    print(f"Saved summary statistics to: {SUMMARY_FILE}")
    print(f"Saved intensity composition table to: {COMPOSITION_FILE}")
    print(f"Saved Mann-Kendall and Theil-Sen trends to: {TREND_FILE}")


if __name__ == "__main__":
    main()
