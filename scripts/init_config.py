from __future__ import annotations

from pathlib import Path
import sys
import textwrap
from typing import List

import yaml  # requires `uv add pyyaml`
from tkinter import Tk, filedialog

CONFIG_PATH = Path("config.local.yml")


def ask(prompt: str, default: str | None = None) -> str:
    """Ask for a value, optionally with a default."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()
        if value:
            return value
        if default is not None:
            return default
        print("Please enter a value.")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question with a default."""
    suffix = "Y/n" if default else "y/N"

    while True:
        value = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def pick_single_csv(title: str) -> str:
    """Open a dialog to pick a single CSV file."""
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title=title,
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    root.destroy()

    if not path:
        print("No file selected. Aborting.", file=sys.stderr)
        sys.exit(1)

    return path


def pick_multiple_csvs(title: str) -> List[str]:
    """Open a dialog to pick one or more CSV files."""
    root = Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title=title,
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    root.destroy()

    if not paths:
        print("No files selected. Aborting.", file=sys.stderr)
        sys.exit(1)

    return list(paths)


def main() -> None:
    if CONFIG_PATH.exists():
        print(f"{CONFIG_PATH} already exists. Nothing to do.")
        return

    print(
        textwrap.dedent(
            """
            No local config found.
            We'll now create config.local.yml by asking a few questions.
            """
        ).strip()
    )
    print()

    # 1) Primary / first forecast month
    primary_month = ask(
        "Primary (first) forecast month (format: YYYY-MM)",
        default="2025-11",
    )

    # 2) Opening date or "unsure"
    unsure_opening = ask_yes_no(
        "Are you unsure about the exact store opening date?",
        default=True,
    )
    if unsure_opening:
        opening_date = "unsure"
    else:
        opening_date = ask(
            "Store opening date (format: YYYY-MM-DD)",
            default="2025-10-19",
        )

    # 3) PRIMARY CSV first
    print()
    print(
        "Step 1: Select the PRIMARY month CSV (for example, the October data).\n"
        "A file dialog will open now."
    )
    primary_csv = pick_single_csv("Select PRIMARY month CSV (e.g. October)")

    # 4) THEN the rest of the months (multi-select)
    print()
    print(
        textwrap.dedent(
            """
            Step 2: Select the rest of the month CSV files.

            In the next dialog you can select:
              - One file, or
              - Multiple files from the same folder (Ctrl+click or Shift+click).

            These will be treated as the additional months after the primary one.
            """
        ).strip()
    )
    other_csvs = pick_multiple_csvs("Select the remaining month CSV file(s)")

    data_section = {
        "primary_month_csv": primary_csv,
        "other_month_csvs": list(other_csvs),
    }

    cfg = {
        "store_id": ask("Store ID (for example: cx or example_store)", default="example_store"),
        "opening_date": opening_date,
        "forecast": {
            "first_forecast_month": primary_month,
        },
        "data": data_section,
    }

    CONFIG_PATH.write_text(
        yaml.safe_dump(cfg, sort_keys=False),
        encoding="utf-8",
    )

    print()
    print(
        textwrap.dedent(
            f"""
            Done. Created {CONFIG_PATH} with:

              opening_date         = {opening_date}
              first_forecast_month = {primary_month}
              primary_month_csv    = {primary_csv}
              other_month_csvs     = {len(other_csvs)} file(s)

            You can open and edit this file manually any time if you need to adjust paths or values.
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
