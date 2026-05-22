"""
Generate publication-style figures for the Qu2016 method reproduction project.

Outputs:
    outputs/figures/*.png
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
ANNUAL_FILE = ROOT / "data" / "processed" / "city_annual_precip_intensity_indices.csv"
COMPOSITION_FILE = ROOT / "outputs" / "tables" / "city_intensity_composition.csv"
TREND_FILE = ROOT / "outputs" / "tables" / "city_mk_theilsen_trends.csv"
FIG_DIR = ROOT / "outputs" / "figures"

CATEGORY_ORDER = ["light", "moderate", "heavy", "extreme"]
CATEGORY_DISPLAY = {
    "light": "Light\n0.1-10",
    "moderate": "Moderate\n10-25",
    "heavy": "Heavy\n25-50",
    "extreme": "Extreme\n>=50",
}


def configure_matplotlib() -> None:
    # Use mostly English text in figures to avoid Chinese font problems on different computers.
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Microsoft YaHei", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 300
    sns.set_theme(style="whitegrid")


def save_figure(filename: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure: {path}")


def plot_city_map(df: pd.DataFrame) -> None:
    city_df = df[["city", "city_cn", "province", "lon", "lat"]].drop_duplicates()
    plt.figure(figsize=(7, 5))
    sns.scatterplot(
        data=city_df,
        x="lon",
        y="lat",
        hue="province",
        s=120,
        edgecolor="black",
        linewidth=0.7,
    )
    for _, row in city_df.iterrows():
        plt.text(row["lon"] + 0.08, row["lat"] + 0.04, row["city"], fontsize=9)
    plt.title("Typical cities in the middle Yangtze River region", fontsize=13, weight="bold")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend(title="Province", frameon=True)
    save_figure("fig1_city_map.png")


def plot_annual_precip_trend(df: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 5.3))
    sns.lineplot(
        data=df,
        x="year",
        y="annual_precip",
        hue="city",
        marker="o",
        linewidth=1.5,
        markersize=3.5,
    )
    plt.title("Annual precipitation, 2000-2024", fontsize=13, weight="bold")
    plt.xlabel("Year")
    plt.ylabel("Annual precipitation (mm)")
    plt.legend(title="City", ncol=2, frameon=True)
    save_figure("fig2_annual_precip_trend.png")


def plot_intensity_composition(composition: pd.DataFrame) -> None:
    comp = composition.copy()
    comp["category"] = pd.Categorical(comp["category"], CATEGORY_ORDER, ordered=True)
    comp = comp.sort_values(["city", "category"])

    pivot = comp.pivot(index="city", columns="category", values="mean_annual_share").fillna(0)
    pivot = pivot[CATEGORY_ORDER]
    pivot = pivot.loc[pivot["extreme"].sort_values(ascending=False).index]

    plt.figure(figsize=(8.5, 5.2))
    bottom = np.zeros(len(pivot))
    x = np.arange(len(pivot.index))
    for cat in CATEGORY_ORDER:
        values = pivot[cat].to_numpy()
        plt.bar(x, values, bottom=bottom, label=CATEGORY_DISPLAY[cat].replace("\n", " "))
        bottom += values

    plt.xticks(x, pivot.index, rotation=35, ha="right")
    plt.ylim(0, 1.02)
    plt.title("Mean annual precipitation composition by intensity category", fontsize=13, weight="bold")
    plt.xlabel("City")
    plt.ylabel("Share of annual precipitation")
    plt.legend(title="Qu2016 category", frameon=True, bbox_to_anchor=(1.02, 1), loc="upper left")
    save_figure("fig3_intensity_composition.png")


def plot_extreme_ratio_heatmap(df: pd.DataFrame) -> None:
    heatmap_data = df.pivot(index="city", columns="year", values="extreme_amount_ratio")
    city_order = df.groupby("city")["extreme_amount_ratio"].mean().sort_values(ascending=False).index
    heatmap_data = heatmap_data.loc[city_order]

    plt.figure(figsize=(12, 4.8))
    sns.heatmap(
        heatmap_data,
        cmap="YlOrRd",
        linewidths=0.15,
        linecolor="white",
        cbar_kws={"label": "Extreme precipitation share"},
    )
    plt.title("Annual proportion of extreme precipitation (P >= 50 mm/day)", fontsize=13, weight="bold")
    plt.xlabel("Year")
    plt.ylabel("City")
    save_figure("fig4_extreme_ratio_heatmap.png")


def plot_trend_slope_by_city(trend: pd.DataFrame) -> None:
    selected_metrics = ["light_amount", "moderate_amount", "heavy_amount", "extreme_amount"]
    sub = trend[trend["metric"].isin(selected_metrics)].copy()
    sub["category"] = sub["metric"].str.replace("_amount", "", regex=False)
    sub["category"] = pd.Categorical(sub["category"], CATEGORY_ORDER, ordered=True)
    sub["label"] = sub["sen_slope_per_decade"].round(2).astype(str) + sub["significance"].fillna("")

    plt.figure(figsize=(10, 5.6))
    ax = sns.barplot(
        data=sub,
        x="city",
        y="sen_slope_per_decade",
        hue="category",
        hue_order=CATEGORY_ORDER,
    )
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Theil-Sen slope of precipitation amount by intensity category", fontsize=13, weight="bold")
    plt.xlabel("City")
    plt.ylabel("Trend slope (mm/decade)")
    plt.xticks(rotation=35, ha="right")
    plt.legend(title="Category", frameon=True, ncol=2)

    # Add significance markers only; numeric labels are available in the trend table.
    for container in ax.containers:
        labels = []
        for bar in container:
            labels.append("")
        ax.bar_label(container, labels=labels, padding=1, fontsize=8)

    save_figure("fig5_trend_slope_by_city.png")


def plot_method_workflow() -> None:
    plt.figure(figsize=(9, 3.8))
    ax = plt.gca()
    ax.axis("off")
    steps = [
        "Daily precipitation\nOpen-Meteo API",
        "Qu2016 fixed thresholds\nLight / Moderate / Heavy / Extreme",
        "Annual indicators\nAmount, days, proportions",
        "Trend analysis\nMann-Kendall + Theil-Sen",
        "Figures and report\nReproducible workflow",
    ]
    x_positions = np.linspace(0.08, 0.92, len(steps))
    for i, (x, text) in enumerate(zip(x_positions, steps)):
        ax.text(
            x,
            0.5,
            text,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="black", linewidth=1.0),
        )
        if i < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x_positions[i + 1] - 0.08, 0.5),
                xytext=(x + 0.08, 0.5),
                arrowprops=dict(arrowstyle="->", lw=1.2),
            )
    plt.title("Reproducible workflow for reproducing Qu et al. (2016) method", fontsize=13, weight="bold")
    save_figure("fig6_method_workflow.png")


def main() -> None:
    configure_matplotlib()
    for path in [ANNUAL_FILE, COMPOSITION_FILE, TREND_FILE]:
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    df = pd.read_csv(ANNUAL_FILE)
    composition = pd.read_csv(COMPOSITION_FILE)
    trend = pd.read_csv(TREND_FILE)

    plot_city_map(df)
    plot_annual_precip_trend(df)
    plot_intensity_composition(composition)
    plot_extreme_ratio_heatmap(df)
    plot_trend_slope_by_city(trend)
    plot_method_workflow()


if __name__ == "__main__":
    main()
