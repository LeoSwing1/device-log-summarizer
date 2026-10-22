# Device Log Summarizer CLI

A small Python CLI that cleans sensor readings, summarizes device telemetry from CSV, exports JSON, and generates a temperature comparison chart.

## Requirements
- Python 3.9+
- Matplotlib (only required for chart generation)

## Quick start
Place `device_telemetry.csv` in the project directory, then run:

```bash
python main.py device_telemetry.csv
```

This creates:
- `outputs/device_summary.json`
- `outputs/temperature_by_device.png`

To use custom output paths:

```bash
python main.py device_telemetry.csv --json-out outputs/device_summary.json --chart-out outputs/temperature_by_device.png
```

Install chart dependency if needed:

```bash
python -m pip install matplotlib
```

## CSV format
Required columns: `device_id`, `status`, `temperature`.

Rows with missing device IDs or invalid temperatures are skipped. Temperature values are parsed as floats. Devices whose average temperature is above 80.0 are excluded from the final summary, as required by the assessment.

## Tests
Run:

```bash
python -m unittest discover -s tests -v
```

## Assessment notes
The project includes a sample CSV and sample output for a reproducible demonstration. Replace the sample CSV with the assessment-provided `device_telemetry.csv` if one is supplied separately.
