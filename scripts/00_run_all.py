"""
Run the full reproducible workflow for reproducing the Qu et al. (2016)
daily precipitation intensity classification method.

Examples:
    python scripts/00_run_all.py
    python scripts/00_run_all.py --force-download
    python scripts/00_run_all.py --demo
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "01_download_data.py",
    "02_preprocess.py",
    "03_analysis.py",
    "04_visualization.py",
    "05_check_outputs.py",
]


def run_script(script_name: str, *, demo: bool = False, force_download: bool = False) -> None:
    script_path = ROOT / "scripts" / script_name
    cmd = [sys.executable, str(script_path)]

    if script_name == "01_download_data.py":
        if demo:
            cmd.append("--demo")
        if force_download:
            cmd.append("--force-download")

    print(f"\n========== Running {script_name} ==========")
    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Qu2016 precipitation reproduction workflow.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use deterministic synthetic daily precipitation data. No internet access is needed.",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-downloading real data from Open-Meteo in non-demo mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("Project root:", ROOT)
    if args.demo:
        print("Running in DEMO mode with synthetic precipitation data.")
    else:
        print("Running in REAL-DATA mode with Open-Meteo historical weather data.")

    for script in SCRIPTS:
        run_script(script, demo=args.demo, force_download=args.force_download)

    print("\nAll workflow steps finished successfully.")


if __name__ == "__main__":
    main()
