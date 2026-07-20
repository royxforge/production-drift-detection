# Contributing to Production Drift Detection

Thank you for your interest in contributing to Production Drift Detection!
This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project and everyone participating in it is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to
uphold this code. Please report unacceptable behavior to royxforge@gmail.com.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/production-drift-detection.git
   cd production-drift-detection
   ```
3. Add the upstream repository:
   ```
   git remote add upstream https://github.com/royxforge/production-drift-detection.git
   ```

## Development Setup

### Prerequisites

- Python 3.9+
- pip

### Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Optional Dependencies

```bash
pip install -e ".[pytorch]"        # PyTorch model support
pip install -e ".[transformers]"   # HuggingFace support
pip install -e ".[dev]"            # Testing and benchmarking
pip install -e ".[all]"            # Everything
```

### Verify Installation

```bash
python -c "from production_drift_detection.detectors.mmd import MMDDetector; print('Setup OK')"
```

## Coding Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide.
- Use type annotations for all function signatures.
- Maximum line length: 88 characters.
- Use descriptive variable names.
- Document all public classes and functions with docstrings.

### Imports

Organize imports in the following order:

1. Standard library imports
2. Third-party imports
3. Local application imports

## Testing

```bash
pytest tests/ -v
pytest tests/test_detectors.py -v
pytest tests/test_monitors.py -v
pytest tests/test_alerts.py -v
pytest tests/test_drift.py -v
pytest tests/test_correlation.py -v
pytest tests/test_dashboard.py -v
```

### Benchmarks

Before submitting performance-sensitive changes, run the benchmark suite:

```bash
python benchmarks.py
```

Ensure no regressions in detection latency or accuracy.

## Pull Request Process

1. Create a new branch from `main`:
   ```
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with clear, descriptive commit messages.

3. Run tests:
   ```bash
   pytest tests/ -v
   ```

4. If adding a new detector, ensure it follows the unified `fit/score/detect/summary` API.

5. Push your branch and open a Pull Request on GitHub.

6. In your PR description, include:
   - What the change does
   - Any relevant issue numbers
   - How you tested the change
   - Benchmark results if applicable

7. Request review from a maintainer.

## Commit Message Conventions

We follow conventional commit format:

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `benchmark`

Examples:
```
feat(detectors): add new ADWIN-based adaptive windowing detector
benchmark(core): add 20-seed rigorous benchmark suite
docs(readme): update MMD threshold calibration guidance
```

## Issue Reporting

### Bug Reports

When filing a bug report, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior and actual behavior
- Environment details (OS, Python version)
- Relevant code snippets or error logs

### Feature Requests

We welcome feature suggestions! Please include:

- A clear description of the proposed feature
- The motivation or use case
- Any relevant research or references
- Whether you are willing to implement it

Thank you for helping make Production Drift Detection better!
