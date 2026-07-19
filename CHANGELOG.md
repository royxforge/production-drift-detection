# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-20

### Added

- **Community health files**: Added `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `CONTRIBUTING.md` (contribution guidelines), `SECURITY.md` (vulnerability reporting policy), and `CITATION.cff` (citation metadata). These files establish project governance, community participation guidelines, and academic attribution framework.

---

## [0.1.0] - 2026-07-14

### Added

- **Model Integration Adapters:**
  - `SklearnAdapter` for Scikit-learn model wrappers enabling unified predict interfaces with integrated drift and confidence monitoring.
  - `PyTorchAdapter` for PyTorch model wrappers with GPU support, softmax probability extraction, and confidence scoring.
  - `HFAdapter` for HuggingFace Transformers integration with text classification pipelines, initially defaulting to DistilBERT SST-2, with configurable model selection and device placement.

- **Confidence Monitoring System:**
  - `ConfidenceMonitor` class tracking mean confidence, predictive entropy, classification margin (top-2 gap), trend direction, expected calibration error approximation, and overconfidence or underconfidence ratios across prediction batches.

- **Stream Monitoring Infrastructure:**
  - `StreamMonitor` for batch ingestion workflows with rolling statistics, automatic detector coordination, and multi-detector fusion for status reporting.

- **Empirical Validation Framework:**
  - `empirical_validation.py` with a 30-trial experimental protocol across 3 experiment types and 10 random seeds, testing the hypothesis that confidence degradation precedes drift detection under gradual covariate shift.
  - `empirical_validation_results.txt` documenting the findings across LogisticRegression and PyTorch NN model classes, two drift types (covariate shift and perturbation), and three detectors (KL, PSI, MMD).

- **Rigorous Benchmark Suite:**
  - `run_benchmark.py` and `benchmark_rigorous.py` implementing a 20-seed, 5-feature, 2000-sample reference evaluation with drift magnitude 2.0 across 10-batch ramp and 40-batch full-strength duration.
  - Metrics reporting with mean plus or minus 2x standard error of the mean for approximate 95% confidence intervals, including false positive rate, detection rate, ROC AUC, Cohen's d, composite rank, and detection latency.

- **Documentation Consolidation:**
  - Production usage guide and comprehensive project Q&A added to project documentation.
  - All separate research notes merged into the primary README.md. The separate `docs/` directory was removed.

### Changed

- **Package Rename:** The package was renamed from `DriftWatch` (v0.1.0 initial release) to `production-drift-detection` to better reflect the production monitoring scope and to align with the new namespace structure under `src/production_drift_detection/`.
- **README.md Updates:** Multiple revisions improving documentation clarity, updating benchmark result tables, fixing formatting, and advancing the software year to 2026.
- **Threshold Calibration Guidance:** Documentation now recommends MMD as the primary detector (zero false positive rate, perfect AUC, immediate detection) with KL Divergence as a secondary signal, and advises recalibration of PSI and ADWIN thresholds before production deployment based on empirical benchmark results.

### Research Findings

- An empirical study across 30 trials found that the confidence-drift lead-lag relationship is detector-dependent and non-deterministic under gradual covariate shift. Confidence precedes drift in 20 to 40 percent of trials depending on the detector and model class combination. The hypothesis that confidence reliably precedes drift (H1) was not supported.
- Cross-correlation analysis confirmed meaningful co-movement between confidence and drift signals, with maximum correlations ranging from 0.38 to 0.77 across detectors, indicating that confidence tracks drift even when it does not reliably precede it.

## [0.1.0-alpha] - 2026-06-06

### Added

- **Core Drift Detection Library:**
  - Four drift detectors with a unified `fit`, `score`, `detect`, and `summary` API:
    - `KLDivergenceDetector`: Kullback-Leibler divergence with Laplace smoothing for numerical stability. Achieves zero false positive rate and ROC AUC of 0.9995 under benchmark conditions.
    - `PSIDetector`: Population Stability Index using binned proportion comparisons. Standard convention thresholds (stable below 0.1, moderate shift 0.1 to 0.25, significant shift above 0.25).
    - `MMDDetector`: Maximum Mean Discrepancy with RBF kernel and median heuristic for automatic bandwidth selection. Top-ranked detector with zero false positive rate and perfect ROC AUC of 1.0.
    - `ADWINDetector`: Adaptive Windowing for online drift detection using Hoeffding-bound change detection without requiring full historical data storage.

- **Alerting System:**
  - Four-tier alert severity levels: Healthy, Watch, Warning, Critical.
  - `AlertRule` schema and `AlertEngine` for threshold-based and rolling-window rule evaluation.
  - Configurable rule definitions and structured alert output with timestamps.

- **Synthetic Drift Generator:**
  - `DriftGenerator` class supporting 8 drift types: covariate shift, prior shift, gradual drift, sudden drift, missingness drift, feature perturbation, Gaussian noise, and feature corruption.
  - Reproducible random state control and configurable number of features.

- **Interactive Dashboard:**
  - FastAPI backend with 6-page Chart.js frontend: Overview, Drift Monitoring, Feature Analysis, Confidence Monitoring, Confidence-Drift Correlation, and Alerts.
  - Real-time score trending, per-feature drift heatmaps, and filterable alert log with severity indicators.

- **Evaluation and Benchmarking:**
  - `BenchmarkFramework` class with standardized benchmark runner, sensitivity analysis across drift magnitudes, and comprehensive metric reporting.
  - Standard benchmark runner in `benchmarks.py` with results output to `benchmark_results.txt`.

- **Utility Modules:**
  - Statistical functions for distribution comparison and confidence intervals.
  - Input validation decorators for detector parameters and data shapes.
  - Structured logging with configurable verbosity levels.

- **Test Suite:**
  - Unit tests covering all detectors, monitors, alerts, correlation analysis, dashboard components, and drift generation.
  - Integration tests for cross-module workflows.

### Changed

- Repository restructured from flat layout to organized module hierarchy under `src/production_drift_detection/` with subpackages for detectors, monitors, alerts, correlation, data, integrations, evaluation, dashboard, and utilities.

### Notes

- This project was originally released under the name DriftWatch before being renamed to production-drift-detection in a subsequent revision.
- This alpha release establishes the core library architecture and API contracts. Threshold calibration for PSI and ADWIN detectors was identified as a necessary step before production deployment, with optimal thresholds of 0.1898 and 0.3778 respectively (versus default 0.1).
- The MMD detector demonstrated optimal calibration at threshold 0.0108 versus the default 0.05, though the performance gain from recalibration was marginal (F1 improvement of 0.0006).
