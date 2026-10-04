# Future Agentic Extension: Replenishment Exception Agent

## Status and boundary

This is a follow-up plan, not part of the current forecasting and replenishment
roadmap. The existing P0-P11 sequence remains unchanged. Agent development starts
only after the batch pipeline produces evaluated forecasts and reproducible order
recommendations.

The extension should be deployed as a separate service or repository. It consumes
published pipeline artifacts; it does not modify forecasting models, reconciliation,
inventory simulation, or ordering-policy logic.

## Product definition

Build one central **Replenishment Exception Agent** across all stores and SKUs.
Do not create one agent per store or product.

The deterministic system continues to calculate forecasts, risks, costs, and valid
order quantities. The agent investigates unusual recommendations, gathers evidence,
compares approved scenarios, explains the trade-off, and requests planner approval.

Example:

> Store 17 normally orders 200 units, but the replenishment engine recommends 500.
> The agent checks forecast drivers, promotion timing, inventory, open purchase
> orders, supplier delay, and policy constraints. It presents the evidence and the
> cost/service trade-off, then asks the responsible planner to approve or reject the
> engine-generated quantity.

## Operating flow

```text
Forecast and replenishment batch
        -> deterministic exception detection
        -> prioritised exception queue
        -> agent gathers evidence through typed tools
        -> replenishment engine evaluates allowed scenarios
        -> agent explains recommendation and alternatives
        -> policy and confidence gate
        -> planner approval
        -> optional downstream order action
        -> immutable decision and outcome record
```

## Historical replay experiment

The agent is evaluated through a hidden 8-12 week historical replay. Actual
demand in that period remains real and completely unavailable to every system
until each simulated day is reached. The operational context around that demand
is generated: opening inventory, open purchase orders, receipts, supplier lead
times, delays, short shipments, MOQ, pack sizes, order calendars, shelf life,
spoilage, and costs.

At each decision date, a system sees only information that would have been
available on that date. It places or changes an order, the simulator advances,
and realised demand and supplier events are applied. This prevents future actuals
from leaking into forecasts or agent decisions.

Use the same held-out demand, initial state, supplier parameters, and random seed
for three comparison arms:

1. **Static baseline** - forecast once at the start and follow the fixed
   replenishment policy without replanning.
2. **Dynamic deterministic baseline** - update forecasts and recompute the policy
   on the configured cadence, without an agent.
3. **Dynamic agentic system** - use the same dynamic forecasts and policy engine,
   while the agent investigates exceptions and selects only from approved,
   engine-evaluated actions.

The second arm is required. Without it, normal rolling replanning could be
incorrectly reported as value created by the agent.

Run paired simulations across multiple seeds for stochastic supplier behavior.
Compare fill rate, stockout units, spoilage, average inventory, working capital,
expedite cost, markdown cost, and total cost. Also report the agent's incremental
result against the dynamic deterministic baseline and the distribution across
seeds, not only one favorable run.

The main result should have this form:

```text
static baseline -> dynamic deterministic improvement
dynamic deterministic -> incremental agent improvement
```

An oracle allowed to see the held-out demand may be reported only as an upper
bound. It is never a competing production policy.

## Responsibility split

| Component | Responsibility |
|---|---|
| Forecasting models | Produce point and quantile demand forecasts |
| Reconciliation | Make hierarchy-level forecasts coherent |
| Replenishment engine | Calculate order quantities, service levels, and costs |
| Deterministic rules | Detect exceptions and enforce business constraints |
| Decision router | Classify cases, select investigation path, confidence-gate |
| LLM supervisor | Gather evidence, compare tool results, and explain recommendations |
| Planner | Approve consequential operational actions |

A typed decision model such as Jev may be used for bounded routing and confidence
gates. It must not calculate order quantities. A generative model may interpret
notes and produce explanations, but all numerical claims must come from tools.

## Initial exception types

Start with a small set whose outcomes can be measured:

1. High projected stockout risk.
2. High projected overstock or spoilage risk.
3. Order quantity materially different from recent orders.
4. Open purchase order likely to arrive late.
5. Promotion or holiday inconsistent with forecast inputs.
6. Forecast interval unusually wide or calibration deteriorating.
7. Missing, stale, or contradictory operational data.

Exception thresholds live in typed configuration. They are not inferred or changed
by the agent.

## Agent tools

The first version is read-only and receives only typed tools:

```text
get_exception(case_id)
get_forecast(store, sku, horizon, quantiles)
get_forecast_evidence(store, sku, horizon)
get_inventory_position(store, sku)
get_open_purchase_orders(store, sku)
get_supplier_constraints(supplier_id)
get_promotion_calendar(store, sku, horizon)
compare_replenishment_scenarios(case_id, scenario_ids)
get_policy_result(case_id)
request_planner_approval(proposal)
record_planner_decision(case_id, decision, reason_code)
```

Tools own validation, authorization, calculations, and database access. The agent
never receives arbitrary SQL or shell access.

## Case and recommendation contracts

Each exception is processed as an independent case:

```text
ExceptionCase
    case_id
    run_id
    store_id
    sku_id
    exception_type
    observed_state
    expected_state
    business_impact
    evidence_refs
    allowed_actions
    assigned_planner
```

The agent must return a structured proposal:

```text
Recommendation
    case_id
    reason_codes
    evidence_refs
    recommended_action
    quantity_from_engine
    scenario_comparison
    expected_service_level
    expected_cost
    confidence
    approval_required
```

No recommendation is valid without evidence references and an order quantity
produced by the replenishment engine.

## Delivery plan

### A0 - Prerequisites

- P7 has selected and calibrated forecast models.
- P8 produces reproducible inventory and supplier mechanics.
- P9 produces evaluated replenishment policies and order recommendations.
- P10 publishes versioned run artifacts and manifests.
- P11 defines monitoring and operational ownership.

### A1 - Exception foundation

- Define `ExceptionCase`, `Evidence`, and `Recommendation` schemas.
- Implement deterministic exception detectors.
- Create a prioritised case queue using estimated business impact.
- Build read-only query tools over pipeline outputs.
- Produce a non-agent baseline report for comparison.

Exit: identical inputs create identical cases, priorities, and evidence references.

### A2 - Read-only investigation agent

- Add one supervisor with a bounded tool allowlist.
- Route each case to demand, inventory, supplier, promotion, or data-quality checks.
- Generate a concise evidence-backed case summary.
- Escalate when data is missing or confidence is below threshold.

Exit: the agent cannot change orders or operational data, and every statement is
traceable to a tool result.

### A3 - Scenario and recommendation layer

- Define a small catalogue of allowed scenarios.
- Run scenarios inside the deterministic replenishment engine.
- Compare fill rate, spoilage, working capital, and total cost.
- Return a structured recommendation with alternatives.

Exit: all quantities and metrics reproduce directly from persisted scenario output.

### A4 - Human approval workflow

- Route cases to the responsible planner.
- Support approve, reject, modify, and request-more-evidence outcomes.
- Capture structured reason codes and comments.
- Record model, prompt, tool calls, evidence, proposal, and decision.

Exit: no consequential action occurs without valid authorization and an idempotency
key.

### A5 - Controlled execution

- Add an ERP or purchase-order adapter only after A1-A4 meet their targets.
- Start in shadow mode, then proposal-only mode.
- Allow automatic action only for explicitly approved low-risk categories.
- Enforce value limits, supplier constraints, rollback procedures, and kill switch.

Exit: duplicate actions are impossible, unauthorized actions are rejected, and every
write has a complete audit trail.

### A6 - Evaluation and monitoring

- Exception precision and missed-exception rate.
- Unsupported-claim rate.
- Confidence calibration and correct-escalation rate.
- Planner handling time and recommendation acceptance.
- Cost and service impact against the deterministic baseline.
- Unsafe-action and duplicate-action counts.
- Data, forecast, decision, and operational drift.

Planner acceptance is diagnostic, not the objective. The business objective remains
cost and service performance under explicit constraints.

## Data interface

### Already available or produced by the existing roadmap

- Favorita sales by date, store, and family.
- Promotion indicators.
- Store, city, state, cluster, and type metadata.
- Holiday calendar, transactions, and oil series.
- Clean daily demand panel.
- Planned quantile forecasts, reconciliation outputs, backtest metrics, and
  calibration results.
- Planned simulated inventory ledger, purchase orders, receipts, supplier master,
  lead times, MOQ, pack sizes, order calendars, reliability, shelf life, and spoilage.
- Planned replenishment recommendations, scenario costs, service levels, and run
  manifests.

### Needed for a real operational deployment

- Current on-hand, reserved, and available inventory.
- Open purchase orders, promised dates, actual ETAs, receipts, and cancellations.
- Product master: SKU, pack size, MOQ, shelf life, unit cost, selling price, and
  markdown or disposal cost.
- Supplier master: lead-time history, reliability, order calendar, and constraints.
- Confirmed future promotions, price changes, holidays, and assortment status.
- Observed stockouts or lost-sales estimates to distinguish zero demand from no stock.
- Planner ownership, authorization limits, and approval routing.
- Historical planner overrides with structured reason codes.
- Final order, receipt, sales, waste, fill-rate, and cost outcomes for evaluation.

The simulated P8 tables are sufficient for research and a portfolio demonstration.
They are not substitutes for live ERP, inventory, supplier, and approval data in a
production deployment.

## Guardrails and non-goals

- No agent-created demand forecasts or order quantities.
- No autonomous changes to models, thresholds, costs, or policies.
- No free-form database or shell access.
- No order submission in the first release.
- No self-modifying production prompts or skills.
- No multi-agent swarm unless measured workload demonstrates that one bounded
  supervisor cannot meet latency or quality requirements.
- No store-level permanent agents; store and SKU are case attributes.

The intended product is a controlled decision workflow around a trusted analytical
system, not an autonomous replacement for the replenishment engine or planner.
