"""Command-line interface for ProductionDriftDetection.

Runs a drift detector over one column of a CSV file and emits a
machine-readable report, so drift checks can run from cron, CI, or any
orchestrator without writing Python first::

    driftdetect generate-sample --output sample.csv
    driftdetect detect --input sample.csv --column feature_0 --detector psi
    driftdetect detect --input scores.csv --column score --fail-on-drift

Exit codes: ``0`` clean, ``1`` drift detected (only with ``--fail-on-drift``),
``2`` invalid usage or unreadable input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from production_drift_detection import __version__
from production_drift_detection.detectors.adwin import ADWINDetector
from production_drift_detection.detectors.base import BaseDetector
from production_drift_detection.detectors.kl import KLDivergenceDetector
from production_drift_detection.detectors.mmd import MMDDetector
from production_drift_detection.detectors.psi import PSIDetector

DETECTORS: dict[str, type[BaseDetector]] = {
    "psi": PSIDetector,
    "kl": KLDivergenceDetector,
    "mmd": MMDDetector,
    "adwin": ADWINDetector,
}

DEFAULT_THRESHOLD = 0.1


def _load_column(path: Path, column: str) -> np.ndarray:
    """Load a single numeric column from ``path``, dropping missing values."""
    if not path.exists():
        raise FileNotFoundError(f"input file not found: {path}")
    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 - surfaced as a CLI usage error
        raise ValueError(f"could not parse {path} as CSV: {exc}") from exc

    if column not in frame.columns:
        available = ", ".join(map(str, frame.columns[:10]))
        raise ValueError(f"column {column!r} not in {path.name} (columns: {available})")

    values = pd.to_numeric(frame[column], errors="coerce").dropna().to_numpy(dtype=float)
    if values.size < 10:
        raise ValueError(
            f"column {column!r} has only {values.size} numeric values; at least 10 are required"
        )
    return values


def _build_detector(name: str, threshold: float) -> BaseDetector:
    if name not in DETECTORS:
        raise ValueError(f"unknown detector {name!r}; choose from {', '.join(DETECTORS)}")
    return DETECTORS[name](threshold=threshold)


def run_detect(
    values: np.ndarray,
    detector_name: str,
    threshold: float = DEFAULT_THRESHOLD,
    reference_fraction: float = 0.5,
) -> dict:
    """Fit on the leading portion of ``values`` and detect drift on the rest."""
    if not 0.0 < reference_fraction < 1.0:
        raise ValueError("--reference-fraction must be strictly between 0 and 1")

    split = int(len(values) * reference_fraction)
    if split < 1 or len(values) - split < 1:
        raise ValueError("reference fraction leaves an empty reference or current window")

    reference = values[:split]
    current = values[split:]

    detector = _build_detector(detector_name, threshold)
    # Detectors accept (n_samples, n_features); a single CSV column is one feature.
    detector.fit(reference.reshape(-1, 1))
    result = detector.detect(current.reshape(-1, 1))

    return {
        "detector": result["detector"],
        "score": float(result["score"]),
        "threshold": float(result["threshold"]),
        "drift_detected": bool(result["drift_detected"]),
        "severity": result.get("severity"),
        "reference_rows": int(len(reference)),
        "current_rows": int(len(current)),
        "summary": detector.summary(),
    }


def _cmd_detect(args: argparse.Namespace) -> int:
    try:
        values = _load_column(Path(args.input), args.column)
        report = run_detect(
            values,
            detector_name=args.detector,
            threshold=args.threshold,
            reference_fraction=args.reference_fraction,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report.update(
        {
            "tool": "production-drift-detection",
            "version": __version__,
            "input": str(args.input),
            "column": args.column,
        }
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    verdict = "DRIFT DETECTED" if report["drift_detected"] else "no drift"
    print(
        f"{args.column}: {verdict} "
        f"(score={report['score']:.4f}, threshold={report['threshold']:.4f}, "
        f"detector={report['detector']}, severity={report['severity']})"
    )
    if args.output:
        print(f"report written to {Path(args.output).resolve()}")

    if args.fail_on_drift and report["drift_detected"]:
        return 1
    return 0


def _cmd_generate_sample(args: argparse.Namespace) -> int:
    """Write a self-contained CSV with a shifted second half (demonstrates drift)."""
    rng = np.random.default_rng(args.seed)
    split = int(args.rows * 0.5)
    feature = rng.normal(loc=0.0, scale=1.0, size=args.rows)
    feature[split:] = rng.normal(loc=args.shift, scale=1.0, size=args.rows - split)

    frame = pd.DataFrame({"feature_0": feature})
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)
    print(f"wrote {len(frame)} rows to {out_path.resolve()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driftdetect",
        description="Run a drift detector over a CSV column and emit a JSON report.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    detect = subparsers.add_parser("detect", help="Detect drift in a CSV column")
    detect.add_argument("--input", "-i", required=True, help="Path to a CSV file")
    detect.add_argument("--column", "-c", required=True, help="Numeric column to analyse")
    detect.add_argument(
        "--detector",
        "-d",
        default="psi",
        choices=sorted(DETECTORS),
        help="Drift detector to use (default: psi)",
    )
    detect.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Alert threshold (default: {DEFAULT_THRESHOLD})",
    )
    detect.add_argument(
        "--reference-fraction",
        type=float,
        default=0.5,
        help="Leading share of rows used as reference data (default: 0.5)",
    )
    detect.add_argument("--output", "-o", help="Write the JSON report to this path")
    detect.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit with status 1 when drift is detected (for CI/cron gates)",
    )
    detect.set_defaults(func=_cmd_detect)

    sample = subparsers.add_parser(
        "generate-sample", help="Write a demo CSV whose second half is shifted"
    )
    sample.add_argument("--output", "-o", default="sample.csv", help="Destination CSV path")
    sample.add_argument("--rows", type=int, default=1000, help="Number of rows (default: 1000)")
    sample.add_argument(
        "--shift", type=float, default=2.0, help="Mean shift applied after the midpoint"
    )
    sample.add_argument("--seed", type=int, default=42, help="Random seed")
    sample.set_defaults(func=_cmd_generate_sample)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
