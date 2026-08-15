# AGENTS.md

Instructions for any AI coding agent working in this repository.

**Read this file first, every session.**

---

## 1. Before you write any code

Read these two files in full:

| File | What it governs |
|---|---|
| `constitution.md` | The business problem (§1 — read it, every scope call traces back to it), then the rules that never change: build sequence, coding standards, analytical non-negotiables, data contract, metrics, scope |
| `roadmap.md` | The 14 phases, what each one builds, and the exit criteria that end it |

Do not skim them. Do not summarise them and proceed. The rules are specific and
several of them are counter-intuitive — you will violate them if you work from
general good practice instead of from these documents.

`decisions.md` also exists. **Do not read, edit, or write to it.** It is the
user's own log.

---

## 2. Authority order

When two things conflict, resolve in this order:

1. `constitution.md`
2. `roadmap.md`
3. The user's instruction in the current session
4. Your own judgement

If the user asks for something that violates the constitution, **say so and
stop.** Do not quietly comply, and do not comply while adding a warning
afterwards. Name the rule, explain the conflict, and wait.

---

## 3. Start-of-session routine

1. Read `constitution.md` and `roadmap.md`
2. Identify the current phase — the earliest one whose exit criteria are not all
   ticked
3. State which phase you are in before writing anything
4. Work only inside that phase

If you cannot tell which phase is current, ask. Do not guess.

---

## 4. Rules you will most likely break

These are the ones that go wrong in practice. They are all in the constitution;
they are repeated here because they are the failure modes.

**Sequence**
- EDA comes before features. Features come before models. Models come before
  the decision layer. No exceptions, no "quick" ones.
- Do not start the next phase until the current phase's exit criteria all pass.
- Do not skip P4 (baselines and backtest harness). Every comparison afterwards
  depends on it.

**Code**
- **No nested functions.** No `def` inside a `def`. Ever.
- Classes follow SOLID. Adding a fourth forecasting model must require zero
  edits to `BacktestRunner`.
- Type hints on every public signature.
- Notebooks import from the package. The package never imports from notebooks.
- No magic numbers. Everything in config.

**Analysis**
- No lookahead. At forecast origin `t`, nothing touches data from `t` onward —
  including rolling stats, scalers, MinT covariance, and hyperparameter tuning.
- Every hierarchy level must sum exactly to total. Assert it.
- Every model must output quantiles, not just point forecasts.
- No MAPE at the bottom level.

**Results**
- A model performing worse than expected is a **result**, not a bug. Record it.
  Do not tune until it wins.
- Never claim an improvement without a number produced by code in this repo, on
  a stated holdout.

---

## 5. Scope control

The constitution has an explicit out-of-scope list. If you think something on it
would improve the project — deep learning forecasters, multi-echelon,
optimisation solvers, real-time serving, an agentic layer — **do not build it.**

Say this instead:

> "Candidate for `decisions.md`: [idea]. Out of scope for the current phase."

Then continue with the phase. The user decides what gets logged and what gets
added.

---

## 6. When you finish a piece of work

State plainly:

- Which exit criteria this satisfies
- Which remain open
- Anything you did that deviates from the constitution, and why

Do not mark a phase complete. Report the criteria status and let the user
decide.

---

## 7. When something goes wrong

Apply constitution §11 (Conflict resolution). In short:

| Situation | Action |
|---|---|
| A non-negotiable is violated | Stop. Fix. Do not proceed. |
| A model underperforms | Record it as a finding. Do not tune it away. |
| The phase is running long | Cut scope inside the phase. Never skip exit criteria. |
| A better idea appears | Name it as a candidate. Do not implement it. |
| Reality contradicts the constitution | Flag it. The user updates the document. |

Never silently work around a rule. A workaround you don't mention becomes a
defect nobody can find later.

---

## 8. Git workflow

**One branch per phase.** Name it after the phase:
`p1-ts-eda`, `p4-baselines`, `r1-forecasting-package`.

**Commit freely on the branch.** Small, described commits as you work. No
permission needed.

**Halt before pushing.** When a phase's exit criteria are met:

1. Stop.
2. Report the criteria status — which passed, which remain open.
3. State the branch name and summarise what the commits contain.
4. **Ask whether to push.** Wait for an explicit yes.

Do not push, open a pull request, or merge without being told to. Not for a
"clean" phase, not for a small fix, not because the work is obviously finished.

**Never:**
- commit directly to `main`
- force-push anything
- merge your own branch
- commit `outputs/`, data files, notebook execution output, or credentials
- amend or rewrite history on a pushed branch

**If a phase is abandoned or reworked**, say so and ask what to do with the
branch. Do not delete it yourself.

---

## 9. Tone

Be direct. If an approach is wrong, say it is wrong and say why. Do not soften
technical disagreement, and do not add praise before criticism.

If a result is disappointing, report the result. This project's value depends on
its numbers being trustworthy, and a flattering number is worse than a bad one.
