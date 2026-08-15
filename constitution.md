# Constitution

Rules that do not change. If this file conflicts with `roadmap.md`, with a
coding agent's suggestion, or with something that seems more convenient in the
moment — **this file wins**.

---

## 1. Business problem

A retail assortment of thousands of SKUs across dozens of stores. Replenishment
is decided on trailing averages. The result is overstock that ends in markdown,
alongside stockouts on the items customers actually came for. Both erode margin
at the same time.

The reason is that the forecast is a single number. Told "next week is 100", a
planner has no basis for choosing 100, 130 or 160 — so the buffer is set by
habit, identically for a fast stable SKU and a slow erratic one, and with no
regard for the fact that a lost sale and a marked-down unit cost different
amounts.

**What this project builds:** an order quantity that follows from the demand
distribution, the cost of being short, and the cost of being long.

**Success test:** a planner can be told *if you want to be in stock 95% of the
time instead of 90%, here is what it costs you in markdown.*

**Mission:**
EDA → features → forecast → reconcile → order decision → ordering lifecycle →
deployable pipeline.

---

## 1a. Data path — decided, do not deviate

### Forecasting data: REAL

Corporación Favorita, from Kaggle competition
`store-sales-time-series-forecasting`. Downloaded once, never modified.

```
data/raw/favorita/
    train.csv              3,000,888 rows
    stores.csv             54 rows
    oil.csv                1,218 rows
    holidays_events.csv    350 rows
    transactions.csv       83,488 rows
```

`data/raw/` is **read-only**. Nothing in this project writes to it.

### Ordering data: SIMULATED — and this is deliberate

**There is no public dataset containing inventory position, reorder decisions,
purchase orders and goods receipts alongside demand.** This is structural, not a
search failure: sales data gets published, stock positions do not.

So the ordering half is generated in P8. The rule that makes it defensible:

> **Demand is always real. Only the mechanics are simulated.**

| Comes from Favorita (real) | Generated in P8 (simulated) |
|---|---|
| daily unit demand per store-family | on-hand inventory position |
| promotions | supplier lead time |
| holidays, oil, transactions | purchase orders and goods receipts |
| store attributes | partial receipts, short shipments |
| | MOQ, pack size, order calendar |
| | shelf life and spoilage |

Never generate synthetic demand. The simulator wraps mechanics around real
demand — that is the whole point, and it is what makes the results meaningful.

Simulation parameters are calibrated against published distributions where
available (BPI Challenge 2019 for PO-to-receipt intervals; DataCo for
promised-vs-actual delay) and documented as stated assumptions where not. Every
parameter carries its source.

### Full path through the project

| Phase | Reads | Writes |
|---|---|---|
| P0 load | `data/raw/favorita/*.csv` | `data/interim/panel.parquet` |
| P1–P2 EDA | `data/interim/panel.parquet` | `outputs/figures/` |
| P3 features | `data/interim/panel.parquet` | `data/processed/features.parquet` |
| P4 baselines | `data/processed/features.parquet` | `outputs/metrics/baselines/` |
| P5 models | `data/processed/features.parquet` | `outputs/forecasts/base/` |
| P6 reconcile | `outputs/forecasts/base/` | `outputs/forecasts/reconciled/` |
| P7 evaluate | `outputs/forecasts/*` | `outputs/metrics/`, `outputs/figures/` |
| **P8 simulate** | `data/interim/panel.parquet` | `data/processed/orders/*.parquet` |
| P9 policies | reconciled forecasts + orders | `outputs/orders/`, `outputs/metrics/` |
| P10 pipeline | all of the above | `outputs/runs/<run_id>/` |

`data/` and `outputs/` are gitignored. Nothing downstream reads a notebook —
every phase reads a file written by the phase before it.

---

## 2. Build sequence — non-negotiable order

```
EDA (time series first)
   → EDA (supporting, only where TS EDA raised a question)
      → feature building
         → baselines + backtest harness
            → model building
               → reconciliation
                  → evaluation
                     → refactor to package
                        → ordering data simulation
                           → refactor
                              → ordering algorithms
                                 → refactor
                                    → integration
                                       → CI/CD + monitoring
```

**No stage may start before the one before it is finished.**

The single most common failure in this kind of project is building features
before understanding the series, or building a decision layer on a forecasting
layer that was never properly evaluated. The decision layer will run, produce
numbers, and be meaningless.

**Every analysis phase is a notebook. Every refactor phase produces `.py`.**
Notebooks are for thinking and showing. Packages are for running. Never deploy a
notebook; never explore inside a package.

---

## 3. Coding standards — non-negotiable

**C1. No nested functions.** No `def` inside a `def`. Ever. If you need shared
state, that is a class. If you need a helper, that is a module-level function.

**C2. Classes follow SOLID.**

- **S — Single responsibility.** One class, one reason to change. A forecaster
  forecasts. It does not load data, engineer features, or write files.
- **O — Open/closed.** Adding a fourth model must not require editing the
  evaluation code. New behaviour comes from new classes, not new `if` branches.
- **L — Liskov substitution.** Any `Forecaster` must be usable wherever the base
  is expected. If `ProphetForecaster` needs a special call sequence the others
  don't, the abstraction is wrong.
- **I — Interface segregation.** Small, focused interfaces. A model that cannot
  produce quantiles should not inherit a `predict_quantiles` method it raises on.
- **D — Dependency inversion.** High-level code depends on abstractions.
  `BacktestRunner` takes a `Forecaster` protocol, never a concrete `SarimaxModel`.

**C3. Explicit interfaces.** Every abstraction is a `Protocol` or `ABC` with
typed signatures. No duck typing across module boundaries.

**C4. No hidden state.** No module-level mutable globals. Configuration is
passed in, never reached out for.

**C5. Type hints on every public function and method.** Enforced in CI.

**C6. Functions do one thing.** If a docstring needs the word "and" to describe
the return value, split it.

**C7. No magic numbers.** Every constant lives in config with a name.

**C8. Notebooks import from the package; the package never imports from
notebooks.** One direction only.

---

## 4. Analytical non-negotiables

**N1. Real demand, simulated mechanics.** Demand always comes from Favorita
actuals. Never generate synthetic demand. Only inventory mechanics — stock
position, lead time, receipts, spoilage — are simulated, because no public
dataset contains them.

**N2. No lookahead. Ever.** At forecast origin `t`, nothing may touch data after
`t`. This includes rolling statistics computed over the full series, scalers
fitted on train+test, MinT covariance estimated on residuals spanning test
periods, and hyperparameters tuned on the final holdout. Enforced by assertion,
not by care.

**N3. Every hierarchy level sums exactly to total.** Asserted in code, on every
fold. If series are dropped, all aggregates are recomputed from the survivors —
never reused.

**N4. Identical evaluation for every model.** Same folds, same origins, same
refit cadence. Any asymmetry invalidates the comparison.

**N5. No MAPE, ever.** ~31% of bottom-level observations are zero; MAPE is
undefined there and sMAPE is not a fix. Metrics and their scaling-denominator
rules are defined in §9 — including the leading-zero rule, which is the most
likely silent error in this project.

**N6. Point forecasts are not the output.** Every model must produce quantiles.
A point forecast cannot drive an order decision. This is a hard interface
requirement, not a nice-to-have — the ordering layer depends on it.

**N7. Costs are explicit parameters.** Underage (`Cu`) and overage (`Co`) live in
config. No hardcoded service levels. Every result stated against a stated cost
ratio.

**N8. Nothing is claimed that isn't measured.** No README or write-up states an
improvement without a number produced by code in this repo, on a stated holdout.

**N9. Reproducible or it didn't happen.** Every run is deterministic from a
seed. Dependencies pinned. Folds derived from config, never hand-typed.

---

## 5. Scope boundaries

**In scope**
- Time-series EDA and supporting EDA
- Feature engineering with leakage controls
- Hierarchical forecasting, different model per level
- **MinT reconciliation** (retained — this is the spine of the forecasting story)
- Quantile / newsvendor decision layer
- Simulated ordering lifecycle (PO, receipt, inventory, supplier)
- Ordering policy comparison against a cost function
- Deployable batch pipeline with CI/CD and monitoring

**Out of scope — do not let these creep in**
- Deep learning forecasters (TFT, N-BEATS, foundation models)
- Multi-echelon networks (single echelon only)
- Routing, assortment, or network design optimisation
- Real-time / streaming inference
- A UI beyond plots, tables, and an optional read-only API
- Nowcasting — deliberately parked, separate learning track
- Agentic layers — candidate for a follow-up project, not this one

Anything rejected goes in `decisions.md` so it is not re-raised in a month.

---

## 6. Data contract

**Primary: Corporación Favorita** (Kaggle: store-sales-time-series-forecasting)

- 3,000,888 rows, 2013-01-01 to 2017-08-15
- 54 stores × 33 families = 1,782 bottom series
- Files: `train.csv`, `stores.csv`, `oil.csv`, `holidays_events.csv`,
  `transactions.csv`

**Known data facts — handle these explicitly, do not rediscover them**

| Fact | Required handling |
|---|---|
| 25 Dec rows are *absent*, not zero (4 dates) | Reindex to a full calendar before any lag feature, or lags silently skip a day |
| 53 series never sell at all | Drop, then recompute aggregates (see N3) |
| 25% of series have >365 leading zeros | Truncate each series at first non-zero — pre-launch zeros are not demand |
| `oil.csv` has 43 nulls (weekends) | Forward-fill. Oil is known for the future, so it is a valid future regressor |
| `holidays_events` has transferred / bridge / work-day types | A `transferred=True` day behaves as a *normal* day; the effect sits on the `Transfer` row. Model this properly or the holiday work is decorative |
| 38 dates carry more than one holiday | Holiday features must handle overlap, not overwrite |
| Bottom level ~31% zeros; upper levels 0–5% | Drives model assignment (§7) |

---

## 7. Model-to-level assignment

Assignment is driven by **measured** intermittency, not preference.

| Level | Approx. zero rate | Model | Reason |
|---|---|---|---|
| Total / state / city | 0–5% | SARIMAX | dense, strong weekly ACF, real exog |
| Store / cluster / family | 1–15% | Prophet | holiday structure lives here |
| Store-family (bottom) | ~31% | LightGBM (quantile objective) | handles zeros, pools across series |

Reconciliation: **MinT-shrink**, always benchmarked against base (unreconciled)
and bottom-up.

**Critical distinction, state it explicitly in any write-up:** different grain
across *competing* models is a confound. Different grain *within one hierarchy,
then reconciled* is the method. The claim is "the right model at each level,
reconciled into a coherent whole" — never "model X beat model Y" when they ran
at different levels.

A model may be swapped only if the intermittency measurement changes, and the
change is recorded in `decisions.md`.

---

## 8. Evaluation protocol

- **Grain:** weekly. Quarter-ahead daily fights three hard problems at once.
- **Horizon:** 13 weeks (one quarter).
- **Validation:** walk-forward, expanding window, 4 non-overlapping folds.
- **Refit:** every fold, every model.
- **Report:** per-level **and** the weighted aggregate. Never the aggregate
  alone — the whole thesis is that different models win at different levels.
- **Spread:** mean and range across folds, never mean alone.
- **Metrics:** see §9. Metric choice and the scaling-denominator rules are
  defined there and nowhere else.

---

## 9. Metrics — definitions and denominator rules

Metrics live here, in one place. Do not define them anywhere else.

### Which metric, where

| Purpose | Metric | Notes |
|---|---|---|
| Point accuracy, all levels | **RMSSE** | primary; comparable across series |
| Point accuracy, secondary | **MASE** | more robust to outliers than RMSSE |
| Quantile accuracy | **Pinball loss** | at each configured quantile |
| Quantile calibration | **Empirical coverage** | does q80 actually cover ~80%? |
| Direction of error | **Mean bias** | reported alongside, never alone |
| Aggregate across levels | Weighted RMSSE | weights stated; **never reported without the per-level table** |

**Banned outright**
- **MAPE** — undefined at zero. ~31% of bottom-level observations are zero.
- **sMAPE** — unstable near zero and asymmetric. Not a fix for MAPE.
- **R²** — meaningless for forecast accuracy on count data.

### The scaling denominator — get this right or every number is wrong

RMSSE and MASE both divide the forecast error by a **naive error** computed on
the training data:

```
naive_error = mean(|y_t − y_{t−1}|)   over the in-sample period
```

This denominator is where these metrics break. Three rules:

**D1. Compute the denominator on post-truncation training data only.**

Leading zeros are pre-launch periods — the product did not exist. Every
consecutive difference across them is zero, which drags the denominator toward
zero. Dividing by a near-zero denominator inflates the score enormously for a
forecast that was perfectly reasonable.

Concretely: a series with 400 pre-launch zeros can produce a denominator around
0.14 instead of around 4.2 — roughly a **30× difference in the reported score,
for an identical forecast.** It affects the ~25% of series with long pre-launch
periods, so it silently distorts the league table without ever looking broken.

The constitution already requires truncating leading zeros before modelling
(§6). **That truncation must also apply to the metric denominator.** Truncating
for the model and scaling on the full series is a real and easy mistake.

**D2. Denominator uses the training window of that fold only.**

Never the full series, never anything after the forecast origin. This is N2
applied to metrics.

**D3. Series that launch inside the test window are excluded from aggregate
scores and reported separately.**

Their denominator would be computed over a period in which they did not exist.
There is no valid scaling factor. Count them, name them, score them separately
if at all.

### Guards — assert these, do not trust them

- [ ] Denominator is strictly greater than a configured floor. If not, the
      series is excluded and logged — never silently divided by.
- [ ] Denominator length equals the post-truncation training length.
- [ ] Count of excluded series reported with every results table. A quietly
      shrinking series count is how a metric bug hides.
- [ ] Seasonal-naive variant (`|y_t − y_{t−m}|`) uses the same three rules.

### Reporting rules

- Per-level **and** per-intermittency-segment. An aggregate alone hides which
  model won where, which is the entire thesis.
- Mean **and** range across folds. Never a single mean.
- Excluded-series count, every time.
- The denominator rule in force, stated once in the write-up.

---

## 10. Decision layer rules

- Order quantity comes from a **quantile of the predictive distribution**, never
  from a point forecast.
- Critical ratio = `Cu / (Cu + Co)`. Stated, never assumed.
- Always report the **service-level vs waste frontier**, not one operating point.
- The textbook newsvendor assumes single-period, no carryover. This system is
  multi-period with shelf life. **The empirical optimum will not equal the
  theoretical critical ratio.** Explain the gap; do not hide it.
- MinT reconciles point forecasts, not quantiles. Reconciled quantiles are not
  the quantiles of the reconciled distribution. Pick an approach, state it, note
  the limitation.

---

## 11. Engineering rules

- **Polars or DuckDB.** Not pandas. Favorita melts to millions of rows.
- **Config over constants.** Costs, lead times, shelf life, fold dates, seeds —
  one config module, typed.
- **Seed everything.** Every run reproducible from its seed.
- **Assertions over comments.** N2 and N3 are asserts that fail loudly.
- **Tests arrive with the code, not at the end.** Every refactor phase ships
  tests. Tests deferred to the CI phase make CI theatre.
- **Deployment target is a batch pipeline on a scheduler.** Not an API.
  Replenishment runs on an order calendar, and MinT needs all levels present
  simultaneously — a per-SKU endpoint cannot reconcile anything. An optional
  read-only API may sit in front of the results table.
- **One installable package**, three subpackages: `forecasting`, `simulation`,
  `ordering`. Single version, single CI.

---

## 12. Conflict resolution

When something goes wrong mid-build, apply in this order:

1. **A rule in §3 or §4 is violated** → stop, fix, do not proceed.
2. **A model performs worse than expected** → that is a *result*, not a bug.
   Record it. Do not tune until it wins.
3. **A phase is running long** → cut scope inside the phase, never skip exit
   criteria.
4. **A better idea appears** → write it in `decisions.md` as a candidate. Do not
   implement it in the current phase.
5. **Reality contradicts this document** → update this document explicitly, with
   a dated entry in `decisions.md`. Never let code and constitution silently
   diverge.

---

## 13. Definition of done

The project is complete when one command runs the batch pipeline and produces:

1. Reconciled, coherent forecasts across all levels for a held-out quarter
2. A per-level accuracy table with fold-level spread
3. Quantile forecasts with a calibration check
4. An order quantity per SKU-store for the next period
5. A service-level vs waste frontier chart
6. A cost comparison: ordering to point forecast vs ordering to the correct
   quantile
7. Green CI, passing tests, and defined monitoring metrics

If a reader can see all seven, the project stands on its own.
