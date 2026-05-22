"""
Check whether all key outputs exist after running the workflow.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "data/raw/city_daily_precip_2000_2024.csv",
    "data/raw/download_metadata.txt",
    "data/processed/city_annual_precip_intensity_indices.csv",
    "outputs/tables/city_summary_statistics.csv",
    "outputs/tables/city_mk_theilsen_trends.csv",
    "outputs/tables/city_intensity_composition.csv",
    "outputs/figures/fig1_city_map.png",
    "outputs/figures/fig2_annual_precip_trend.png",
    "outputs/figures/fig3_intensity_composition.png",
    "outputs/figures/fig4_extreme_ratio_heatmap.png",
    "outputs/figures/fig5_trend_slope_by_city.png",
    "outputs/figures/fig6_method_workflow.png",
]


def main() -> None:
    missing = []
    for rel_path in REQUIRED_FILES:
        path = ROOT / rel_path
        if not path.exists() or path.stat().st_size == 0:
            missing.append(rel_path)

    if missing:
        raise FileNotFoundError("Missing required output files:\n" + "\n".join(missing))

    annual = pd.read_csv(ROOT / "data/processed/city_annual_precip_intensity_indices.csv")
    trend = pd.read_csv(ROOT / "outputs/tables/city_mk_theilsen_trends.csv")
    composition = pd.read_csv(ROOT / "outputs/tables/city_intensity_composition.csv")

    assert not annual.empty, "Annual index table is empty."
    assert not trend.empty, "Trend table is empty."
    assert not composition.empty, "Composition table is empty."
    assert {"light_amount", "moderate_amount", "heavy_amount", "extreme_amount"}.issubset(annual.columns)
    assert {"mk_p", "sen_slope_per_decade", "significance"}.issubset(trend.columns)

    print("All required outputs exist and basic table checks passed.")


if __name__ == "__main__":
    main()
