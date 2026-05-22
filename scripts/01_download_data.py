"""
Download or generate daily precipitation data.

Real-data mode:
    Downloads daily precipitation from Open-Meteo Historical Weather API.

Demo mode:
    Generates deterministic synthetic daily precipitation data so that the
    workflow can be tested offline on any computer.

Outputs:
    data/raw/city_daily_precip_2000_2024.csv
    data/raw/download_metadata.txt
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import time
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CITY_FILE = DATA_DIR / "city_locations.csv"
OUTPUT_FILE = RAW_DIR / "city_daily_precip_2000_2024.csv"
METADATA_FILE = RAW_DIR / "download_metadata.txt"

START_DATE = "2000-01-01"
END_DATE = "2024-12-31"
API_URL = "https://archive-api.open-meteo.com/v1/archive"

DEFAULT_CITY_DATA = [
    {"city": "Wuhan", "city_cn": "武汉", "province": "Hubei", "lon": 114.3054, "lat": 30.5928, "region_note": "Middle Yangtze core city"},
    {"city": "Yichang", "city_cn": "宜昌", "province": "Hubei", "lon": 111.2864, "lat": 30.6919, "region_note": "Downstream of Three Gorges Reservoir region"},
    {"city": "Jingzhou", "city_cn": "荆州", "province": "Hubei", "lon": 112.2397, "lat": 30.3352, "region_note": "Jianghan Plain and Yangtze River bank city"},
    {"city": "Changsha", "city_cn": "长沙", "province": "Hunan", "lon": 112.9388, "lat": 28.2282, "region_note": "Xiangjiang River basin representative city"},
    {"city": "Yueyang", "city_cn": "岳阳", "province": "Hunan", "lon": 113.1289, "lat": 29.3571, "region_note": "Dongting Lake region representative city"},
    {"city": "Nanchang", "city_cn": "南昌", "province": "Jiangxi", "lon": 115.8582, "lat": 28.6820, "region_note": "Poyang Lake plain representative city"},
    {"city": "Jiujiang", "city_cn": "九江", "province": "Jiangxi", "lon": 115.9928, "lat": 29.7120, "region_note": "Yangtze River and Poyang Lake junction city"},
]


def ensure_directories() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs" / "figures").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs" / "tables").mkdir(parents=True, exist_ok=True)


def ensure_city_file() -> None:
    if CITY_FILE.exists():
        return
    city_df = pd.DataFrame(DEFAULT_CITY_DATA)
    city_df.to_csv(CITY_FILE, index=False, encoding="utf-8-sig")
    print(f"Created default city file: {CITY_FILE}")


def read_existing_mode() -> str | None:
    if not METADATA_FILE.exists():
        return None
    text = METADATA_FILE.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if line.lower().startswith("mode:"):
            return line.split(":", 1)[1].strip().lower()
    return None


def generate_demo_city_daily_precip(row: pd.Series, dates: pd.DatetimeIndex, city_index: int) -> pd.DataFrame:
    """Generate deterministic synthetic rainfall data for offline testing."""
    rng = np.random.default_rng(seed=202606 + city_index)
    day_of_year = dates.dayofyear.to_numpy()
    years = dates.year.to_numpy()

    # A monsoon-like seasonal rainfall probability and city-specific wetness.
    seasonal = 0.5 + 0.5 * np.sin(2 * np.pi * (day_of_year - 145) / 365.25)
    city_wetness = 0.75 + 0.08 * city_index
    trend = 1.0 + 0.004 * (years - years.min())
    wet_probability = np.clip(0.10 + 0.45 * seasonal * city_wetness, 0.03, 0.78)

    is_wet = rng.random(len(dates)) < wet_probability
    base_amount = rng.gamma(shape=1.4 + 0.05 * city_index, scale=7.5 * city_wetness, size=len(dates))

    # Inject occasional heavy and extreme events to exercise all Qu2016 categories.
    heavy_boost = rng.random(len(dates)) < (0.020 + 0.003 * city_index)
    extreme_boost = rng.random(len(dates)) < (0.004 + 0.001 * city_index)
    precip = np.where(is_wet, base_amount * trend, 0.0)
    precip = np.where(heavy_boost & is_wet, precip + rng.uniform(20, 45, len(dates)), precip)
    precip = np.where(extreme_boost & is_wet, precip + rng.uniform(45, 90, len(dates)), precip)
    precip = np.round(precip, 2)

    return pd.DataFrame(
        {
            "date": dates,
            "precipitation_mm": precip,
            "city": row["city"],
            "city_cn": row["city_cn"],
            "province": row["province"],
            "lon": row["lon"],
            "lat": row["lat"],
            "data_mode": "demo",
        }
    )


def request_city_daily_precip(row: pd.Series) -> pd.DataFrame:
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "The 'requests' package is required for real-data mode. "
            "Run 'python -m pip install -r requirements.txt' first, or use '--demo'."
        ) from exc

    params = {
        "latitude": row["lat"],
        "longitude": row["lon"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "precipitation_sum",
        "timezone": "Asia/Shanghai",
    }

    response = requests.get(API_URL, params=params, timeout=90)
    response.raise_for_status()
    data = response.json()

    if "daily" not in data or "time" not in data["daily"]:
        raise ValueError(f"Unexpected API response for {row['city']}: {data}")

    daily = pd.DataFrame(
        {
            "date": data["daily"]["time"],
            "precipitation_mm": data["daily"]["precipitation_sum"],
        }
    )
    daily["city"] = row["city"]
    daily["city_cn"] = row["city_cn"]
    daily["province"] = row["province"]
    daily["lon"] = row["lon"]
    daily["lat"] = row["lat"]
    daily["data_mode"] = "real_open_meteo"
    return daily


def save_metadata(mode: str, row_count: int, city_count: int) -> None:
    metadata = f"""
Mode: {mode}
Created time: {datetime.now().isoformat(timespec='seconds')}
Data source: {'Synthetic deterministic demo data' if mode == 'demo' else 'Open-Meteo Historical Weather API'}
API endpoint: {API_URL if mode != 'demo' else 'Not used in demo mode'}
Start date: {START_DATE}
End date: {END_DATE}
Daily variable: precipitation_sum
Timezone: Asia/Shanghai
Number of cities: {city_count}
Number of rows: {row_count}
Output file: {OUTPUT_FILE.relative_to(ROOT)}
""".strip()
    METADATA_FILE.write_text(metadata, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download or generate daily precipitation data.")
    parser.add_argument("--demo", action="store_true", help="Generate synthetic demo data instead of downloading.")
    parser.add_argument("--force-download", action="store_true", help="Force real-data download even if raw file exists.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_directories()
    ensure_city_file()

    existing_mode = read_existing_mode()
    if OUTPUT_FILE.exists() and not args.demo and not args.force_download and existing_mode != "demo":
        print(f"Raw data already exists: {OUTPUT_FILE}")
        print("Skip downloading. Use --force-download to download again.")
        return

    city_df = pd.read_csv(CITY_FILE)
    all_records = []

    if args.demo:
        print("Generating deterministic synthetic daily precipitation data for offline demo mode...")
        dates = pd.date_range(START_DATE, END_DATE, freq="D")
        for idx, row in city_df.iterrows():
            print(f"Generating demo data for {row['city']}...")
            all_records.append(generate_demo_city_daily_precip(row, dates, int(idx)))
        mode = "demo"
    else:
        if existing_mode == "demo" and OUTPUT_FILE.exists() and not args.force_download:
            print("Existing raw file was generated in demo mode. It will be replaced by real Open-Meteo data.")
        for _, row in city_df.iterrows():
            print(f"Downloading daily precipitation for {row['city_cn']} ({row['city']})...")
            all_records.append(request_city_daily_precip(row))
            time.sleep(1)
        mode = "real_open_meteo"

    result = pd.concat(all_records, ignore_index=True)
    result["date"] = pd.to_datetime(result["date"])
    result["precipitation_mm"] = pd.to_numeric(result["precipitation_mm"], errors="coerce").fillna(0)
    result = result.sort_values(["city", "date"]).reset_index(drop=True)
    result.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    save_metadata(mode=mode, row_count=result.shape[0], city_count=city_df.shape[0])

    print(f"Saved daily precipitation data to: {OUTPUT_FILE}")
    print(f"Saved metadata to: {METADATA_FILE}")


if __name__ == "__main__":
    main()
