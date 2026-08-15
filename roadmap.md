# Roadmap

Fourteen phases in four blocks. Each phase has **exit criteria** — a phase is
done when the boxes tick, not when it feels done.

**Rule: do not start the next phase until the current one's criteria pass.**

**Phase types**
- **NB** — notebook section. Exploration and demonstration.

**Three notebooks only.** Several phases share a notebook, in order, as separate
sections:

| Notebook | Phases |
|---|---|
| `01_eda_features.ipynb` | P1 time-series EDA → P2 supporting EDA → P3 features |
| `02_modeling_inference.ipynb` | P4 baselines → P5 models → P6 reconciliation → P7 evaluation |
| `03_replenishment.ipynb` | P8 simulation → P9 ordering policies |

Sharing a notebook does **not** merge the phases. Each phase is a marked section
with its own exit criteria, completed in order. A notebook is not finished until
every phase inside it has passed.

Each notebook ends by writing its artifact to disk (constitution §1a). The next
notebook reads that file — never a variable held in memory from the notebook
before.
- **PKG** — refactor. Notebook code becomes SOLID classes in `src/`. Ships tests.
- **OPS** — integration and deployment.

---

## Repo layout (established in P0, never reorganised later)

Which phase reads and writes which file: **constitution §1a**. Do not invent paths.

```
data/
    raw/favorita/   Kaggle source files — READ ONLY, gitignored
    interim/        panel.parquet — gitignored
    processed/      features.parquet, orders/ — gitignored
notebooks/
    01_eda_features.ipynb        P1 → P2 → P3
    02_modeling_inference.ipynb  P4 → P5 → P6 → P7
    03_replenishment.ipynb       P8 → P9
src/replenish/
    config/         typed config, no magic numbers
    data/           loaders, validators
    features/       feature builders
    forecasting/    models, reconciliation, backtest
    simulation/     ordering lifecycle generator
    ordering/       policies, newsvendor, cost model
    pipeline/       orchestration
tests/              mirrors src/ structure
outputs/            artifacts — never committed
```

---

# BLOCK A — Forecasting

## P0 · Setup and data foundation — **PKG**

**Build**
- Repo skeleton exactly as above
- `config/` — typed settings: paths, cost params, fold dates, seeds, sim params
- `data/loaders.py` — a `DataLoader` class per source (Favorita, stores, oil,
  holidays, transactions). One class, one source (C2-S)
- `data/validators.py` — a `Validator` protocol; one validator class per rule
  from constitution §6
- Pinned dependencies, seeded RNG

**Exit criteria**
- [ ] Row count is exactly 3,000,888 before reindexing
- [ ] After reindexing, every series has an unbroken daily index (the 4 missing
      Christmas dates are filled)
- [ ] 53 all-zero series identified and dropped; count logged
- [ ] Leading zeros truncated per series; count logged
- [ ] Oil forward-filled, zero nulls remaining
- [ ] All validators pass; each has a unit test
- [ ] Two runs from the same seed produce byte-identical output

**Do not** start modelling here. Not even one quick ARIMA.

---

## P1 · Time-series EDA — **NB** `01_eda_features.ipynb` § time series

**This phase comes before everything analytical.** Every later decision —
features, model choice, grain — is justified by what is found here.

**Build**
- Series inventory: count, length, start dates, dead series
- **Intermittency profiling** — zero rate distribution per level; segment series
  into smooth / erratic / intermittent / lumpy
- **Decomposition** — trend, weekly, annual, residual, at each level
- **ACF / PACF** at each level; identify seasonal lags
- **Stationarity** — ADF and KPSS, before and after differencing
- Seasonality strength by segment — is weekly seasonality universal or only for
  fast movers?
- Outliers and closures — Christmas, store-level zero days, one-off spikes
- Distribution of demand: overdispersion, zero inflation, skew
- Level-by-level variance profile — how much noise is averaged away going up

**Exit criteria**
- [ ] Every series assigned to an intermittency segment; counts tabulated
- [ ] Seasonal lags identified per level with evidence, not assumption
- [ ] Stationarity result recorded per level, with the differencing implied
- [ ] Outlier and closure dates catalogued
- [ ] Grain decision (weekly) either confirmed or challenged **with evidence**
- [ ] Model-to-level assignment (constitution §7) confirmed or challenged
- [ ] A written list of open questions for P2

**This phase's real output is the open-questions list.** P2 exists to answer it.

---

## P2 · Supporting EDA — **NB** `01_eda_features.ipynb` § supporting

**Only investigate what P1 raised.** This is not a general data tour.

**Likely areas**
- **Promo response** — does `onpromotion` shift level, and by how much per family?
- **Holiday effects** — national vs local vs regional; and critically, do
  `transferred=True` days behave like normal days?
- **Oil** — any relationship to demand, at what lag, at what level?
- **Transactions** — is store footfall a useful leading signal or collinear noise?
- Store attributes: does cluster or type explain demand shape?

**Exit criteria**
- [ ] Every open question from P1 answered or explicitly deferred
- [ ] Each candidate exogenous variable has a measured relationship, or is
      rejected with a reason
- [ ] Transferred-holiday behaviour verified empirically — not assumed
- [ ] Feature candidate list produced for P3

**Do not build features here.** Measure relationships; decide in P3.

---

## P3 · Feature building — **NB** `01_eda_features.ipynb` § features

**Build**
- Lag features, per constitution's no-lookahead rule
- Rolling statistics — mean, std, zero-rate, all shifted
- Calendar features — day/week/month, holiday flags by locale, transferred
  handling
- Promo features — current, lagged, rolling intensity
- Exogenous features validated in P2
- Encodings for store, family, cluster, type

**Leakage controls — the point of this phase**
- Every rolling feature computed **within** the training window only
- A test that deliberately introduces a leaked feature and confirms the
  backtest catches it

**Exit criteria**
- [ ] Every feature has a stated rationale traceable to P1 or P2
- [ ] No feature uses data from `t` or later at forecast origin `t` — asserted
- [ ] Leakage canary test passes (leaked feature is detected)
- [ ] Feature importance sanity check on a quick model — nothing suspiciously
      dominant
- [ ] Feature set frozen and documented

---

## P4 · Baselines and backtest harness — **NB** `02_modeling_inference.ipynb` § baselines

**Nothing gets compared to anything without this phase.**

**Build**
- Walk-forward fold generator: 4 expanding-window quarterly folds
- Baselines: seasonal naive, naive, moving average, **Croston / SBA** for
  intermittent series
- Metrics per constitution §9 — RMSSE, MASE, pinball, coverage, bias
- The comparison table format every later phase reports into

**Exit criteria**
- [ ] Fold boundaries printed and eyeballed against the calendar
- [ ] No fold's training window contains any of its own test dates — asserted
- [ ] Baseline scores recorded per level, per fold, with spread
- [ ] Metric implementations unit-tested against hand-computed examples
- [ ] **Scaling denominator computed on post-truncation training data only**
      (constitution §9 D1) — tested with a series carrying long leading zeros
- [ ] Denominator floor guard active; excluded-series count reported
- [ ] Series launching inside a test window identified and excluded (§9 D3)
- [ ] The bar every model must clear is now a number on paper

**Most projects skip this. Every number they report afterwards is unanchored.**

---

## P5 · Model building — **NB** `02_modeling_inference.ipynb` § models

**Build**
- SARIMAX at upper levels — exog: oil, promo intensity, holidays
- Prophet at mid levels — full holiday spec including transferred / bridge /
  work-day
- LightGBM at bottom level — **quantile objective**, pooled across series

**Hard requirement:** every model outputs quantiles, not just a mean
(constitution N6). The ordering layer depends on it. A model that ships point
forecasts fails this phase.

**Exit criteria**
- [ ] Every model beats its baseline at its own level — **or the loss is
      recorded as a finding and not tuned away**
- [ ] Every model outputs the configured quantile set
- [ ] Quantile calibration checked: does q80 cover ~80%?
- [ ] Per-level, per-fold results with spread
- [ ] Runtime per fold recorded
- [ ] No-lookahead assertion passes inside every fit

**Expected finding:** Prophet may well lose. Favorita's holiday structure is good
but the exogenous set is still thin. An explained loss beats a forced win.

---

## P6 · Reconciliation — **NB** `02_modeling_inference.ipynb` § reconciliation

**Build**
- Summing matrix `S` for the full hierarchy
- MinT-shrink; also bottom-up and OLS for comparison
- Residual covariance from **training-window residuals only** (N2)
- Negative-value handling: NNLS or clipping — decide and record

**Exit criteria**
- [ ] `S @ bottom == all_levels` to floating-point tolerance, every fold
- [ ] Coherence error of the *base* forecasts measured — the gap MinT closes
- [ ] Three sets compared: base, bottom-up, MinT-shrink
- [ ] Reconciled forecasts sum exactly — asserted
- [ ] Negative-value approach chosen and recorded in `decisions.md`
- [ ] Per-level RMSSE before vs after reconciliation

**If MinT does not beat bottom-up, that is a real result.** It happens more than
the literature suggests. Do not hide it.

---

## P7 · Evaluation and selection — **NB** `02_modeling_inference.ipynb` § evaluation

**Build**
- Consolidated per-level, per-fold comparison across all models and baselines
- Winner per level, per intermittency segment
- Error decomposition: bias vs variance, by horizon step
- Quantile calibration plots
- Where does error concentrate — which levels, which segments, which weeks?

**Exit criteria**
- [ ] One table that answers "which model, which level, and why"
- [ ] Horizon degradation curve — how much worse is week 13 than week 1?
- [ ] Calibration verified for the quantile that will drive ordering
- [ ] Final model-per-level configuration frozen
- [ ] Every claim in the write-up traceable to a cell in this notebook

---

## R1 · Refactor → `src/replenish/forecasting/` — **PKG**

**Build**
- `Forecaster` protocol: `fit(X, y)`, `predict(X)`, `predict_quantiles(X, qs)`
- `SarimaxForecaster`, `ProphetForecaster`, `LgbmQuantileForecaster` — each
  substitutable for the protocol (C2-L)
- `Reconciler` protocol; `MinTShrink`, `BottomUp`, `OlsReconciler`
- `BacktestRunner` — depends on the protocols, never on concrete classes (C2-D)
- `FeaturePipeline` — composable transformers
- Metrics module

**Exit criteria**
- [ ] Zero nested functions in `src/` — enforced by lint rule
- [ ] Every class passes a SOLID review against constitution §3
- [ ] Adding a hypothetical fourth model requires **no edit** to `BacktestRunner`
      (open/closed test)
- [ ] Type hints on every public signature; mypy clean
- [ ] Unit tests per class; integration test reproducing P7's headline numbers
- [ ] Notebook results reproduced by the package to within tolerance

---

# BLOCK B — Ordering data

## P8 · Ordering lifecycle simulation — **NB** `03_replenishment.ipynb` § simulation

**Goal:** the transactional tables a real ERP would produce. Single echelon —
store orders direct from supplier.

**The rule (constitution §1a): demand is always real, only mechanics are
simulated.** Read demand from `data/interim/panel.parquet` — Favorita actuals.
Generate only inventory position, lead time, POs, receipts, MOQ, pack size,
order calendar, shelf life and spoilage. **Never generate synthetic demand.**

No public dataset contains inventory position alongside demand, which is why
this phase exists at all. That is a defensible reason, not an apology.

**Tables**
- `purchase_orders` — order_id, sku, store, order_date, qty, promised_date,
  unit_cost, supplier_id
- `goods_receipts` — order_id, receipt_date, qty_received
- `inventory_daily` — store, sku, date, opening, receipts, issues, closing,
  in_transit, spoilage
- `supplier_master` — lead time distribution, MOQ, pack size, order calendar,
  reliability

**Friction that must be present** — without it the tables are toys:
- promised date ≠ actual date
- partial receipts and short shipments
- MOQ and pack-size rounding
- order calendars — cannot order every day
- supplier reliability differing by vendor
- shelf life and FEFO issue order

**Calibration:** parameters set from published distributions where possible;
documented as assumptions where not. Every parameter carries its source.

**Exit criteria**
- [ ] Four tables generate and join cleanly on their keys
- [ ] Inventory identity holds **every day**:
      `closing == opening + receipts − issues − spoilage`
- [ ] Realised lead-time distribution matches the configured parameters
- [ ] Every parameter documented with source or stated assumption
- [ ] Censoring measured: true demand vs observed sales gap
- [ ] Reproducible from seed

---

## R2 · Refactor → `src/replenish/simulation/` — **PKG**

**Build**
- `InventoryLedger` — holds state, enforces the daily identity
- `SupplierModel` — lead time, reliability, MOQ, calendar
- `OrderBook` — POs and receipts
- `SimulationEngine` — orchestrates; takes an ordering policy as a dependency

**Exit criteria**
- [ ] Zero nested functions; SOLID review passed
- [ ] `SimulationEngine` accepts any `OrderingPolicy` without modification
- [ ] Inventory identity enforced by assertion inside the ledger, not by the caller
- [ ] Property test: identity holds across randomised parameter sweeps
- [ ] Notebook results reproduced by the package

---

# BLOCK C — Ordering decisions

## P9 · Ordering algorithms — **NB** `03_replenishment.ipynb` § policies

**Build, in this order:**
1. `(s, Q)` fixed reorder point — the incumbent most retailers actually run
2. `(R, S)` periodic order-up-to
3. Safety stock with lead-time uncertainty
4. **Newsvendor quantile order-up-to** — the one driven by P5's quantiles
5. Base-stock with pipeline visibility — fixes double-ordering

**Also**
- Cost model: `Cu`, `Co`, total cost
- Critical-ratio sweep
- Service-level vs waste frontier

**Exit criteria**
- [ ] All five policies run on identical demand, identical seeds
- [ ] One comparison table: fill rate, spoilage, days of supply, total cost
- [ ] Naive policies genuinely lose, and the reason is diagnosed
- [ ] Cost-ratio sweep shows a real U-shape
- [ ] Gap between theoretical CR and empirical optimum measured **and explained**
      (multi-period carryover + shelf life)
- [ ] Ordering-to-point-forecast vs ordering-to-quantile stated as a cost multiple
- [ ] Sensitivity to lead-time variability, not just the mean case

**This phase is the differentiator.** Everyone forecasts. Almost nobody connects
a forecast to an order quantity.

---

## R3 · Refactor → `src/replenish/ordering/` — **PKG**

**Build**
- `OrderingPolicy` protocol: `order_quantity(state, forecast) -> float`
- One class per policy, all substitutable
- `CostModel` — single responsibility, no policy logic inside it
- `PolicyEvaluator` — depends on protocols only

**Exit criteria**
- [ ] Zero nested functions; SOLID review passed
- [ ] Adding a sixth policy requires no edit to `PolicyEvaluator`
- [ ] Cost model unit-tested against hand-computed cases
- [ ] Notebook results reproduced by the package

---

# BLOCK D — Production

## P10 · Integration — **OPS**

**Build**
- `pipeline/` — one orchestrated batch run:
  `load → validate → features → forecast → reconcile → quantiles → order`
- Single entry point, config-driven
- Artifact persistence: forecasts, orders, metrics, run metadata
- Run manifest: seed, config hash, package version, timestamp

**Exit criteria**
- [ ] One command produces every artifact in constitution §13
- [ ] Pipeline is idempotent — same config and seed give the same output
- [ ] Failure in any stage fails the run loudly; no silent partial output
- [ ] End-to-end integration test on a data subset, running in CI time
- [ ] Run manifest written with every execution

---

## P11 · CI/CD and monitoring — **OPS**

**Build**
- CI: lint (including the no-nested-function rule), mypy, unit tests,
  integration test, coverage gate
- CD: build, version, deploy the batch job to a scheduler
- **Monitoring metrics, defined not just enabled:**
  - *Data drift* — input distribution shift, schema changes, null-rate spikes
  - *Forecast drift* — rolling RMSSE vs the backtest baseline
  - *Calibration decay* — is q80 still covering 80% in production?
  - *Decision drift* — order quantities vs recent history
  - *Cost drift* — realised total cost vs simulated expectation
  - *Operational* — runtime, failures, data freshness
- Alert thresholds and an escalation path for each

**Exit criteria**
- [ ] CI green on a clean clone
- [ ] Lint enforces constitution §3, not just style
- [ ] Coverage gate set and met
- [ ] Deployment reproducible from the repo alone
- [ ] Every monitoring metric has a threshold and an owner
- [ ] A deliberately drifted input triggers the expected alert
- [ ] Rollback procedure documented and tested

---

## Sequencing discipline

| Temptation | Why it fails |
|---|---|
| Skip P1, go straight to features | Every feature choice becomes unjustified |
| Build features before P2 answers the questions | You engineer signals that aren't there |
| Skip P4, compare models directly | Nothing is anchored; "better" is meaningless |
| Ship point forecasts from P5 | P9 needs quantiles; you will rebuild |
| Refactor at the end instead of R1/R2/R3 | Three notebooks of untested code, one week before CI |
| Tune a losing model until it wins | That is the result. Report it |
| Defer tests to P11 | CI becomes theatre |
| Deploy a notebook | Notebooks explore; packages run |
