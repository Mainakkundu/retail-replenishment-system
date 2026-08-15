# Handoff

## Current state

- Branch: `p0-setup`
- Current phase: P0 setup and data foundation
- Remote: `https://github.com/Mainakkundu/retail-replenishment-system.git`
- Do not read, edit, or write `decisions.md` unless the user explicitly changes
  the repo rules.

## What is done

- Git repository initialized.
- Remote `origin` configured.
- Branch `p0-setup` pushed to GitHub.
- Commit identity corrected to `Mainak Kundu <mainakmarket@gmail.com>`.
- P0 scaffold added:
  - package skeleton under `src/replenish/`
  - typed config in `src/replenish/config/settings.py`
  - data loaders, validators, and panel builder in `src/replenish/data/`
  - tests under `tests/`
  - README with Kaggle download instructions
- Constitution updated to allow pandas, NumPy, Polars, and DuckDB.

## Verification already run

```text
.venv/bin/python -m pytest
.venv/bin/ruff check src tests
.venv/bin/mypy src
```

All passed after the latest completed commit.

## Current blocker

The Favorita data has not been downloaded. Kaggle download failed because
`kaggle.json` was missing.

Expected credential path:

```text
data/raw/favorita/.kaggle/kaggle.json
```

Expected raw data files after download and unzip:

```text
data/raw/favorita/train.csv
data/raw/favorita/stores.csv
data/raw/favorita/oil.csv
data/raw/favorita/holidays_events.csv
data/raw/favorita/transactions.csv
```

## Next step

Once Kaggle credentials are present, download/unzip the Kaggle competition data,
then run:

```text
.venv/bin/python -m replenish.data.build_panel
```

After that, validate the P0 exit criteria from `roadmap.md`.

## Git workflow reminder

Work on one branch per phase. Do not merge into `main` without user review and
explicit approval.

