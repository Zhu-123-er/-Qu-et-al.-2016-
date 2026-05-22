"""
Preprocess daily precipitation data and calculate annual intensity indices.

This script reproduces the fixed-threshold daily precipitation classification
used by Qu et al. (2016):
    light:    0.1 <= P < 10 mm/day
    moderate: 10 <= P < 25 mm/day
    heavy:    25 <= P < 50 mm/day
    extreme:  P >= 50 mm/day

Outputs:
    data/processed/city_annual_precip_intensity_indices.csv
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "city_daily_precip_2000_2024.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "city_annual_precip_intensity_indices.csv"

TRACE_THRESHOLD = 0.1
LIGHT_UPPER = 10.0
MODERATE_UPPER = 25.0
HEAVY_UPPER = 50.0

CATEGORY_ORDER = ["light", "moderate", "heavy", "extreme"]
CATEGORY_LABELS = {
    "light": "Light precipitation (0.1-10 mm/day)",
    "moderate": "Moderate precipitation (10-25 mm/day)",
    "heavy": "Heavy precipitation (25-50 mm/day)",
    "extreme": "Extreme precipitation (>=50 mm/day)",
}


def classify_precipitation(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    p = df["precipitation_mm"]
    df["is_dry_day"] = p <= 0
    df["is_trace_day"] = (p > 0) & (p < TRACE_THRESHOLD)
    df["is_wet_day"] = p >= TRACE_THRESHOLD

    df["light_amount"] = np.where((p >= TRACE_THRESHOLD) & (p < LIGHT_UPPER), p, 0.0)
    df["moderate_amount"] = np.where((p >= LIGHT_UPPER) & (p < MODERATE_UPPER), p, 0.0)
    df["heavy_amount"] = np.where((p >= MODERATE_UPPER) & (p < HEAVY_UPPER), p, 0.0)
    df["extreme_amount"] = np.where(p >= HEAVY_UPPER, p, 0.0)

    df["light_days"] = ((p >= TRACE_THRESHOLD) & (p < LIGHT_UPPER)).astype(int)
    df["moderate_days"] = ((p >= LIGHT_UPPER) & (p < MODERATE_UPPER)).astype(int)
    df["heavy_days"] = ((p >= MODERATE_UPPER) & (p < HEAVY_UPPER)).astype(int)
    df["extreme_days"] = (p >= HEAVY_UPPER).astype(int)
    return df


def calculate_annual_indices(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["precipitation_mm"] = pd.to_numeric(df["precipitation_mm"], errors="coerce").fillna(0)
    df.loc[df["precipitation_mm"] < 0, "precipitation_mm"] = 0
    df = classify_precipitation(df)

    group_cols = ["city", "city_cn", "province", "lon", "lat", "year"]
    optional_cols = ["data_mode"]
    if all(col in df.columns for col in optional_cols):
        group_cols.append("data_mode")

    annual = (
        df.groupby(group_cols, as_index=False)
        .agg(
            annual_precip=("precipitation_mm", "sum"),
            valid_days=("precipitation_mm", "count"),
            dry_days=("is_dry_day", "sum"),
            trace_days=("is_trace_day", "sum"),
            wet_days=("is_wet_day", "sum"),
            max_1day_precip=("precipitation_mm", "max"),
            light_amount=("light_amount", "sum"),
            moderate_amount=("moderate_amount", "sum"),
            heavy_amount=("heavy_amount", "sum"),
            extreme_amount=("extreme_amount", "sum"),
            light_days=("light_days", "sum"),
            moderate_days=("moderate_days", "sum"),
            heavy_days=("heavy_days", "sum"),
            extreme_days=("extreme_days", "sum"),
        )
    )

    amount_cols = [f"{cat}_amount" for cat in CATEGORY_ORDER]
    day_cols = [f"{cat}_days" for cat in CATEGORY_ORDER]
    annual["classified_precip"] = annual[amount_cols].sum(axis=1)

    for cat in CATEGORY_ORDER:
        annual[f"{cat}_amount_ratio"] = np.where(
            annual["annual_precip"] > 0,
            annual[f"{cat}_amount"] / annual["annual_precip"],
            np.nan,
        )
        annual[f"{cat}_day_ratio"] = np.where(
            annual["wet_days"] > 0,
            annual[f"{cat}_days"] / annual["wet_days"],
            np.nan,
        )

    annual["classification_coverage"] = np.where(
        annual["annual_precip"] > 0,
        annual["classified_precip"] / annual["annual_precip"],
        np.nan,
    )

    numeric_cols = [
        "annual_precip",
        "max_1day_precip",
        "light_amount",
        "moderate_amount",
        "heavy_amount",
        "extreme_amount",
        "classified_precip",
        "classification_coverage",
    ] + [f"{cat}_amount_ratio" for cat in CATEGORY_ORDER] + [f"{cat}_day_ratio" for cat in CATEGORY_ORDER]

    annual[numeric_cols] = annual[numeric_cols].round(6)
    annual[day_cols + ["valid_days", "dry_days", "trace_days", "wet_days"]] = annual[
        day_cols + ["valid_days", "dry_days", "trace_days", "wet_days"]
    ].astype(int)
    return annual


def main() -> None:
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw data not found: {RAW_FILE}. Run scripts/01_download_data.py first."
        )

    df = pd.read_csv(RAW_FILE)
    annual = calculate_annual_indices(df)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    annual.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Saved annual precipitation intensity indices to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
