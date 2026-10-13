"""Tests for the ``driftdetect`` command-line interface."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from production_drift_detection.cli import build_parser, main


def _write_csv(path, rows=600, shift=0.0) -> str:
    """Write a CSV whose second half is optionally mean-shifted."""
    rng = np.random.default_rng(0)
    values = rng.normal(0.0, 1.0, rows)
    split = rows // 2
    if shift:
        values[split:] = rng.normal(shift, 1.0, rows - split)
    pd.DataFrame({"score": values}).to_csv(path, index=False)
    return "score"


def test_version_flag_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_no_subcommand_prints_help_and_fails(capsys):
    assert main([]) == 2
    assert "usage:" in capsys.readouterr().out


def test_detect_flags_injected_drift(tmp_path):
    csv = tmp_path / "drifted.csv"
    _write_csv(csv, shift=3.0)

    assert main(["detect", "-i", str(csv), "-c", "score"]) == 0

    # Without the gate the presence of drift does not change the exit status.


def test_fail_on_drift_gate_returns_1(tmp_path):
    csv = tmp_path / "drifted.csv"
    _write_csv(csv, shift=3.0)

    code = main(["detect", "-i", str(csv), "-c", "score", "--fail-on-drift"])
    assert code == 1


def test_fail_on_drift_gate_passes_when_clean(tmp_path):
    csv = tmp_path / "clean.csv"
    _write_csv(csv, shift=0.0)

    code = main(["detect", "-i", str(csv), "-c", "score", "--fail-on-drift"])
    assert code == 0


def test_report_json_is_written_and_structured(tmp_path):
    csv = tmp_path / "drifted.csv"
    report = tmp_path / "report.json"
    _write_csv(csv, shift=3.0)

    assert main(["detect", "-i", str(csv), "-c", "score", "-o", str(report)]) == 0

    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["tool"] == "production-drift-detection"
    assert data["detector"] == "PSI"
    assert data["column"] == "score"
    assert data["drift_detected"] is True
    assert data["score"] > data["threshold"]
    assert data["reference_rows"] + data["current_rows"] == 600
    assert data["summary"]["fitted"] is True


def test_unknown_column_returns_usage_error(tmp_path, capsys):
    csv = tmp_path / "drifted.csv"
    _write_csv(csv)

    assert main(["detect", "-i", str(csv), "-c", "does_not_exist"]) == 2
    assert "error:" in capsys.readouterr().err


def test_missing_file_returns_usage_error(tmp_path, capsys):
    missing = tmp_path / "nope.csv"
    assert main(["detect", "-i", str(missing), "-c", "score"]) == 2
    assert "not found" in capsys.readouterr().err


def test_invalid_reference_fraction_returns_usage_error(tmp_path):
    csv = tmp_path / "drifted.csv"
    _write_csv(csv)

    code = main(
        ["detect", "-i", str(csv), "-c", "score", "--reference-fraction", "1.5"]
    )
    assert code == 2


@pytest.mark.parametrize("detector", ["psi", "kl", "mmd", "adwin"])
def test_every_detector_runs(tmp_path, detector):
    csv = tmp_path / "drifted.csv"
    report = tmp_path / f"{detector}.json"
    _write_csv(csv, shift=3.0)

    code = main(
        ["detect", "-i", str(csv), "-c", "score", "-d", detector, "-o", str(report)]
    )
    assert code == 0
    assert report.exists()


def test_generate_sample_is_detectable(tmp_path):
    sample = tmp_path / "sample.csv"
    assert main(["generate-sample", "-o", str(sample), "--rows", "400"]) == 0
    assert sample.exists()

    # generate-sample introduces a mean shift, so the detector must flag it.
    assert main(["detect", "-i", str(sample), "-c", "feature_0", "--fail-on-drift"]) == 1


def test_parser_exposes_expected_options():
    parser = build_parser()
    args = parser.parse_args(
        ["detect", "-i", "a.csv", "-c", "score", "--fail-on-drift", "-o", "r.json"]
    )
    assert args.command == "detect"
    assert args.fail_on_drift is True
    assert args.output == "r.json"
    assert args.detector == "psi"
