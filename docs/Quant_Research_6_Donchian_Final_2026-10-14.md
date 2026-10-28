# Quant Research #6 — Donchian Four-Week Rule
Final report — 2026-10-14

## Verdict

**FAIL / NOT VALIDATED as a serious modern edge under frozen v0.1.**

The historical rule is real and mechanically testable. It worked materially better in the 1985–2009 era than after 2009, but the modern signal is weak, statistically indistinguishable from zero, and inferior to same-risk controls on this dataset.

## Frozen primary implementation

- 84 diversified futures from the same package/data used in Quant Research #2.
- Primary signal: close-confirmed 20-trading-day Donchian channel, continuous long/short state.
- Decision at close t applied to t+1 return.
- Point-in-time EWMA volatility scaling; no stops, discretionary filters, or parameter search.
- Package volume-based transaction-cost estimates, 1x primary; 2x/3x stress.
- Primary credibility period: 2010 onward.

Because the broad 84-market resource contains benchmark/settlement prices rather than daily OHLC, this is explicitly a close-confirmed proxy. A separate high/low diagnostic was run on ES, GC and TY, the three package markets with OHLC.

## Primary results

### 1985–2009

- annual arithmetic net return: **8.94%**
- annual vol: **11.01%**
- Sharpe: **0.812**
- CAGR: **8.68%**
- MaxDD: **-19.17%**

### 2010–2026

Gross before modeled costs:
- annual return: **3.65%**
- Sharpe: **0.314**

Net at primary 1x costs:
- annual return: **0.09%**
- annual vol: **11.65%**
- Sharpe: **0.008**
- CAGR: **-0.58%**
- MaxDD: **-36.86%**
- annual turnover: **153.3x**
- modeled annual cost drag: **3.56%**

12-month block bootstrap for annual arithmetic mean:
- point estimate: **0.04%**
- 95% CI: **[-4.32%, 4.78%]**
- P(mean <= 0): **50.9%**

At 2x costs:
- annual return: **-3.47%**
- Sharpe: **-0.298**

### 2020–2026

- annual return: **2.70%**
- Sharpe: **0.219**
- CAGR: **1.96%**
- MaxDD: **-27.56%**

Recent returns are positive but not strong enough to reverse the post-2009 verdict.

## Literal four-completed-calendar-week robustness

The pre-registered robustness arm comparing each close with the maximum/minimum closes of the four prior completed calendar weeks produced, post-2009:

- annual net return: **0.58%**
- Sharpe: **0.049**

This agrees with the primary conclusion: near-zero modern risk-adjusted performance.

## Controls

Same-risk Always Long, 2010 onward:
- annual return: **9.44%**
- vol: **13.84%**
- Sharpe: **0.683**
- CAGR: **8.85%**

Prior QR2 12-month TSMOM, same data and 1x costs, 2010 onward:
- annual return: **5.87%**
- vol: **12.26%**
- Sharpe: **0.479**
- CAGR: **5.25%**

Therefore the short 4-week channel does not add compelling modern value versus either simple long premia or the slower 12-month trend rule.

## Cost / implementation observation

Daily ex-ante volatility resizing generated high portfolio turnover (~153x/year), so modeled costs consume most of the modest gross edge. This is a legitimate implementation concern, but it does **not** rescue the signal: gross post-2009 Sharpe is only 0.31 with ~3.7% annual arithmetic return before costs, and the primary bootstrap after costs spans zero widely.

Changing sizing/rebalance frequency now would be a new preregistered implementation, not a correction of this result.

## OHLC diagnostic: ES / Gold / 10Y Treasury

The three markets with daily OHLC show some positive post-2009 high/low-channel behavior before explicit trading costs, but only weak-to-moderate standalone Sharpe:

- ES: post-2009 Sharpe 0.155, annual arithmetic 2.71%, MaxDD -41.48%
- GC: post-2009 Sharpe 0.304, annual arithmetic 5.27%, MaxDD -34.80%
- TY: post-2009 Sharpe 0.113, annual arithmetic 0.62%, MaxDD -12.06%

This is not enough to overturn the diversified primary result and is not a broad OOS proof.

## Asset-class attribution post-2009

- Agriculture: +1.66% annual arithmetic contribution
- Energy: +1.06% annual arithmetic contribution
- Bonds: +0.37% annual arithmetic contribution
- STIR: +0.01% annual arithmetic contribution
- Metals: -0.26% annual arithmetic contribution
- FX: -0.76% annual arithmetic contribution
- Equities: -1.99% annual arithmetic contribution

The result is not a universal trend effect across classes; equities and FX detract materially while agriculture and energy contribute most of the positive arithmetic.

## Practical $5k gate

Even if the institutional portfolio had passed statistically, an 84-contract diversified futures implementation with average gross leverage around 8x is not directly implementable with ~$5,000 using ordinary contracts. Micro-futures or a smaller ETF/futures subset would require a new practical implementation test.

Since the signal fails the statistical/benchmark gate first, practical engineering is not justified yet.

## Status

**CLOSED: Donchian Four-Week Rule v0.1 fails as a serious modern retail candidate.**

Do not search breakout windows after seeing this result. Murphy's 1- or 2-week exit variants may only be reopened as a separate preregistered hypothesis, not used to rescue v0.1.
