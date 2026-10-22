#!/usr/bin/env python3
"""Summarize device telemetry CSV data and optionally generate a chart."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def clean_sensor_readings(values: list[Any]) -> list[float]:
    """Convert usable readings to floats, drop invalid/negative values, cap at 500."""
    cleaned: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if number < 0:
            continue
        if number > 500.0:
            number = 500.0
        cleaned.append(number)
    return cleaned


def summarize_csv(csv_path: Path) -> list[dict[str, Any]]:
    """Aggregate valid CSV rows by device, excluding average temperatures > 80."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"temperatures": [], "record_count": 0, "error_count": 0}
    )

    try:
        with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            required = {"device_id", "status", "temperature"}
            headers = set(reader.fieldnames or [])
            missing = required - headers
            if missing:
                raise ValueError("CSV missing required column(s): " + ", ".join(sorted(missing)))

            for line_number, row in enumerate(reader, start=2):
                device_id = (row.get("device_id") or "").strip()
                status = (row.get("status") or "").strip().upper()
                raw_temperature = row.get("temperature")
                if not device_id:
                    print(f"Warning: skipping line {line_number}: missing device_id", file=sys.stderr)
                    continue
                try:
                    temperature = float(raw_temperature)  # type: ignore[arg-type]
                except (TypeError, ValueError, OverflowError):
                    print(f"Warning: skipping line {line_number}: invalid temperature", file=sys.stderr)
                    continue

                if not (temperature == temperature and abs(temperature) != float("inf")):
                    print(f"Warning: skipping line {line_number}: non-finite temperature", file=sys.stderr)
                    continue

                item = grouped[device_id]
                item["temperatures"].append(temperature)
                item["record_count"] += 1
                if status == "ERROR":
                    item["error_count"] += 1
    except UnicodeDecodeError as exc:
        raise ValueError(f"Could not decode CSV as UTF-8: {exc}") from exc

    results: list[dict[str, Any]] = []
    for device_id, values in sorted(grouped.items()):
        temperatures = values["temperatures"]
        if not temperatures:
            continue
        average = sum(temperatures) / len(temperatures)
        if average > 80.0:
            continue
        results.append({
            "device_id": device_id,
            "total_records": values["record_count"],
            "average_temperature": round(average, 2),
            "error_count": values["error_count"],
        })
    return results


def write_json(results: list[dict[str, Any]], output_path: Path) -> None:
    """Write summary results as formatted JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(results, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")


def print_summary_table(results: list[dict[str, Any]]) -> None:
    """Print a compact terminal table without third-party dependencies."""
    columns = [
        ("Device ID", "device_id"),
        ("Records", "total_records"),
        ("Avg Temp", "average_temperature"),
        ("Errors", "error_count"),
    ]
    widths = [max(len(title), *(len(str(row[key])) for row in results)) for title, key in columns]
    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(line)
    print("| " + " | ".join(title.ljust(width) for (title, _), width in zip(columns, widths)) + " |")
    print(line)
    for row in results:
        print("| " + " | ".join(str(row[key]).ljust(width) for (_, key), width in zip(columns, widths)) + " |")
    print(line)
    if not results:
        print("No devices matched the aggregation and temperature filter.")


def generate_chart(json_path: Path, chart_path: Path) -> None:
    """Generate a labeled bar chart from the JSON summary."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Matplotlib is required for chart generation. Install with: python -m pip install matplotlib") from exc

    if not json_path.is_file():
        raise FileNotFoundError(f"JSON summary not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    device_ids = [item["device_id"] for item in data]
    averages = [item["average_temperature"] for item in data]

    chart_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    if device_ids:
        bars = ax.bar(device_ids, averages)
        ax.bar_label(bars, fmt="%.1f", padding=3)
        ax.set_ylim(0, max(averages) * 1.15 if max(averages) > 0 else 1)
    else:
        ax.text(0.5, 0.5, "No qualifying devices", ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    ax.set_title("Average Temperature by Device")
    ax.set_xlabel("Device")
    ax.set_ylabel("Average temperature (°C)")
    ax.tick_params(axis="x", labelrotation=25)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    fig.savefig(chart_path, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize device telemetry CSV data.")
    parser.add_argument("csv_file", type=Path, help="Path to device_telemetry.csv")
    parser.add_argument("--json-out", type=Path, default=Path("outputs/device_summary.json"))
    parser.add_argument("--chart-out", type=Path, default=Path("outputs/temperature_by_device.png"))
    parser.add_argument("--no-chart", action="store_true", help="Skip chart generation")
    args = parser.parse_args()

    try:
        results = summarize_csv(args.csv_file)
        write_json(results, args.json_out)
        print_summary_table(results)
        print(f"\nJSON summary saved to: {args.json_out}")
        if not args.no_chart:
            generate_chart(args.json_out, args.chart_out)
            print(f"Chart saved to: {args.chart_out}")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
