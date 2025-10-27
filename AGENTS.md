# Repository Guidelines

## Project Structure & Module Organization
- `qts/` contains the Quantitative Trading System core modules (risk controls, execution, orchestration). Keep new pipeline logic colocated with adjacent modules (e.g., order routing in `executor.py`).
- `plugins/` hosts marketplace-ready agent plugins; each subdirectory ships a `plugin.json` manifest and optional README describing intended use.
- `config/` stores default runtime JSON (risk configs, provider presets); `schemas/` holds JSON Schema definitions used by validators.
- `scripts/` includes operational utilities such as `validate_marketplace.py`; `examples/` and `data/` provide sample sessions and fixtures for demos; `logs/` retains ACE/QTS run artifacts for troubleshooting.

## Build, Test, and Development Commands
- Create an isolated environment before modifying agents:
  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Run simulated trading sessions locally:
  ```bash
  PYTHONPATH=. python -m qts.main --symbols ETH SOL XRP --llm-provider mock
  ```
- Validate marketplace metadata before publishing:
  ```bash
  python scripts/validate_marketplace.py
  ```

## Coding Style & Naming Conventions
- Python modules use 4-space indentation, type hints, and descriptive docstrings focused on risk assumptions and agent hand-offs.
- Keep filenames and identifiers snake_case; reserve PascalCase for classes and ALL_CAPS for immutable configuration keys.
- Format with `black .` and lint with `flake8 qts plugins` when available; update manifests with minimal JSON diff and sorted keys.

## Testing Guidelines
- Prefer `pytest` for unit and integration coverage; mirror source tree structure under `tests/` (e.g., `tests/test_risk.py` for `qts/risk.py`).
- Record deterministic mocks in `data/fixtures/` and assert against ACE bullet outputs stored under `logs/`.
- Target critical risk and execution paths first; gate new trading modes on simulated drawdown tests before requesting review.

## Commit & Pull Request Guidelines
- Use conventional commits (`feat:`, `fix:`, `docs:`) with imperative subjects summarizing the trading or agent impact.
- Reference linked issues or run IDs in the body, and attach key logs or screenshots for behavior changes.
- PRs should outline validation steps (`pytest`, dry-run command) and highlight any schema or plugin manifest updates for reviewers.

## Security & Configuration Tips
- Never commit API keys or live trading credentials; load them via environment variables or `config/local/*.json` ignored artifacts.
- Keep live-trading toggles disabled by default and document any opt-in flags prominently in the PR description.
