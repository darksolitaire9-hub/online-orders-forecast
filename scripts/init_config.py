from __future__ import annotations

import sys
import textwrap
from datetime import datetime
from pathlib import Path
from tkinter import Tk, filedialog
from typing import List

import yaml  # requires `uv add pyyaml`

CONFIG_PATH = Path("config.local.yml")


def ask(prompt: str, default: str | None = None) -> str:
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


def validate_date(value: str, fmt: str) -> bool:
    """Return True if value matches the datetime format fmt."""
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def ask_date(prompt: str, fmt: str, default: str | None = None) -> str:
    """
    Ask for a date with format validation.
    fmt examples: '%Y-%m' or '%Y-%m-%d'.
    """
    while True:
        value = ask(prompt, default=default)
        if validate_date(value, fmt):
            return value
        print(f"Please enter a date in format {fmt!r} (e.g. {default}).")


def pick_single_csv(title: str) -> str:
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


def pretty_print_config(cfg: dict) -> None:
    """Pretty-print the final YAML config for user confirmation."""
    print()
    print("Final config.local.yml content:")
    print("-" * 40)
    print(
        yaml.safe_dump(
            cfg,
            sort_keys=False,
            indent=2,
            allow_unicode=True,
        ).strip()
    )
    print("-" * 40)


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

    # 1) Primary / first forecast month (with format validation)
    primary_month = ask_date(
        "Primary (first) forecast month (format: YYYY-MM)",
        fmt="%Y-%m",
        default="2025-11",
    )

    # 2) Is the primary month fully covered?
    primary_full = ask_yes_no(
        "Does the primary month CSV contain a full calendar month of data?",
        default=True,
    )

    opening_date: str
    ignore_primary_if_partial_unknown = False

    if primary_full:
        knows_opening = ask_yes_no(
            "Do you know the exact store opening date?",
            default=True,
        )
        if knows_opening:
            opening_date = ask_date(
                "Store opening date (format: YYYY-MM-DD)",
                fmt="%Y-%m-%d",
                default="2025-10-19",
            )
        else:
            opening_date = "unsure"
    else:
        knows_opening = ask_yes_no(
            "Primary month is partial. Do you know the exact store opening date?",
            default=False,
        )
        if knows_opening:
            opening_date = ask_date(
                "Store opening date (format: YYYY-MM-DD)",
                fmt="%Y-%m-%d",
                default="2025-10-19",
            )
        else:
            opening_date = "unsure"
            ignore_primary_if_partial_unknown = ask_yes_no(
                "You have a partial opening month and don't know the exact date.\n"
                "Do you want to IGNORE the primary month CSV entirely "
                "and start from the next full month?",
                default=True,
            )

    # 3) How many months of data total (informational)
    months_count_str = ask(
        "How many months of data do you have in total (including the initial month)?",
        default="2",
    )
    try:
        months_count = int(months_count_str)
    except ValueError:
        print("Invalid number, defaulting to 2 months.")
        months_count = 2

    # 4) PRIMARY CSV
    print()
    print(
        "Step 1: Select the PRIMARY month CSV (for example, the opening or first month).\n"
        "A file dialog will open now."
    )
    primary_csv = pick_single_csv("Select PRIMARY month CSV")
    primary_csv_path = Path(primary_csv).resolve()

    # 5) Remaining CSVs
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
    other_csvs_raw = pick_multiple_csvs("Select the remaining month CSV file(s)")

    # Normalise paths and remove duplicates, especially the primary CSV if re-selected.
    other_paths: list[Path] = []
    seen: set[Path] = set()

    for p in other_csvs_raw:
        resolved = Path(p).resolve()
        if resolved == primary_csv_path:
            continue
        if resolved not in seen:
            seen.add(resolved)
            other_paths.append(resolved)

    if len(other_paths) + 1 != months_count:
        print(
            f"Warning: you said you have {months_count} month(s) of data, "
            f"but after de-duplication we have {1 + len(other_paths)} CSV file(s).",
            file=sys.stderr,
        )

    # 6) Data source (platform tag)
    data_source = ask(
        "Data source / platform (for example: uber_eats, glovo, pos, mixed)",
        default="unknown",
    )

    data_section = {
        "primary_month_csv": str(primary_csv_path),
        "other_month_csvs": [str(p) for p in other_paths],
        "primary_month_full": primary_full,
        "ignore_primary_if_partial_unknown": ignore_primary_if_partial_unknown,
    }

    cfg = {
        "store_id": ask(
            "Store ID (for example: cx or example_store)", default="example_store"
        ),
        "opening_date": opening_date,
        "forecast": {
            "first_forecast_month": primary_month,
        },
        "data_source": data_source,
        "data": data_section,
    }

    # Pretty-print for human check before writing
    pretty_print_config(cfg)

    if not ask_yes_no("Write this configuration to config.local.yml?", default=True):
        print("Aborted by user. No config file written.")
        return

    CONFIG_PATH.write_text(
        yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print()
    print(f"Done. Created {CONFIG_PATH}.")


if __name__ == "__main__":
    main()
