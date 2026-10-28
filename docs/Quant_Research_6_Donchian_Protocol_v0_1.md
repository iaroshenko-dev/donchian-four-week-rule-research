# Quant Research #6 — Donchian Four-Week Rule
Frozen protocol v0.1 — 2026-10-14

## Source rule
Murphy describes Richard Donchian's Four-Week Rule:
1. close shorts / open longs when price exceeds the highs of the last four complete calendar weeks;
2. close longs / open shorts when price falls below the lows of the last four complete calendar weeks.
The classic version is continuous; Murphy also describes 1- or 2-week opposite breakouts as exit-only modifications.

## Research question
Does a simple short-horizon price-channel breakout contain a durable, cost-resistant trend edge in diversified futures, especially after 2009, and does the breakout signal add value versus same-risk non-signal controls?

## Data
Same frozen 84-futures dataset used in Quant Research #2:
- trendfollowing 1.3.1 package resources
- daily continuous benchmark prices
- daily USD excess returns
- supplied time-varying volume-based transaction-cost estimates
- 1959-07-02 to 2026-07-10 (availability varies by contract)

For broad 84-market testing only daily benchmark/settlement prices are available, not OHLC.
Therefore the broad test is explicitly a **close-confirmed proxy**, not a claim to reproduce intraday stop-order fills from the historical book.

Three package markets also have daily OHLC (ES, GC, TY); these are used as a separate high/low validation diagnostic.

## Primary signal — broad 84-market implementation
`DONCHIAN_20D_CLOSE_CONTINUOUS`

For each instrument and day t:
- upper_t = maximum benchmark price over the prior 20 trading observations, excluding t;
- lower_t = minimum benchmark price over the prior 20 trading observations, excluding t;
- if Close_t > upper_t: signal_t = +1;
- if Close_t < lower_t: signal_t = -1;
- otherwise carry the previous signal;
- before the first breakout, exposure is zero.

Decision at close t applies to return t+1. No same-day lookahead.

20 trading observations are frozen as the primary operationalization of four trading weeks.

## Literal-calendar robustness arm — pre-registered before results
`DONCHIAN_4_COMPLETED_WEEKS_CLOSE`

For each day in calendar week W, reference all available daily closes belonging to the four completed ISO weeks W-4...W-1. Current week is excluded.
- Close above the maximum => +1
- Close below the minimum => -1
- otherwise carry previous signal.

This tests the wording "four complete calendar weeks" without changing parameters after results.
It is robustness only and cannot rescue a failed primary.

## OHLC diagnostic arm — ES, GC, TY only
For each day in week W, compute the highest daily HIGH and lowest daily LOW over the four completed prior ISO weeks.
- if current HIGH exceeds prior-4-week high only => +1;
- if current LOW falls below prior-4-week low only => -1;
- if both occur in one daily bar => ambiguous; carry prior signal;
- otherwise carry prior signal.
Position changes apply next day.

This is a diagnostic for whether using high/low rather than closing prices changes the sign materially; three markets are insufficient for the main portfolio verdict.

## Portfolio construction
To separate directional signal from raw contract volatility:
- ex-ante volatility: EWMA of daily USD excess returns, COM=60, annualized with sqrt(261), shifted one day;
- target risk weight per instrument before diversification: 40% / ex-ante vol;
- divide by number of instruments with valid signal/vol that day;
- no ex-post portfolio volatility targeting;
- no stop loss, take profit, regime filter, or asset-class tuning.

This deliberately matches the risk-normalization logic used in Quant Research #2 so Donchian can be compared with TSMOM and same-risk controls.

## Costs
Use the package's frozen daily volume-based cost estimate per 1.0 change in portfolio weight.
Report:
- gross
- 1x costs PRIMARY
- 2x costs
- 3x costs

No cost assumption may be selected because it makes the rule profitable.

## Controls
1. `AlwaysLong_scaled`: same ex-ante vol scaling and availability, signal always +1.
2. Prior Quant Research #2 `TSMOM_scaled` results are used as an external same-dataset benchmark; no parameters are changed.
3. Signal activity/turnover is reported to determine whether results are simply leverage/cost artifacts.

## Fixed periods
- 1985-01-01 through 2009-12-31: historical/discovery-era comparison.
- 2010-01-01 through end of data: PRIMARY modern test.
- 2020-01-01 through end of data: recent regime.

The post-2009 result is the primary credibility test.

## Required metrics
- annualized arithmetic return
- annualized vol
- Sharpe
- CAGR
- max drawdown
- skew
- annual turnover
- annual cost drag
- average gross leverage
- average active instruments
- calendar-year returns
- asset-class attribution if available
- 12-month block-bootstrap CI for annualized arithmetic mean, post-2009 and post-2020

## Verdict gate
A serious signal candidate requires all of:
1. post-2009 net-1x annualized arithmetic return > 0;
2. post-2009 block-bootstrap 95% lower bound > 0;
3. post-2009 Sharpe > 0.4;
4. modestly higher costs (2x) do not erase profitability;
5. no single calendar year contributes more than 50% of post-2009 cumulative arithmetic return;
6. Donchian improves risk-adjusted results versus `AlwaysLong_scaled` or provides meaningful diversification not explained by the same long premia;
7. recent 2020+ result is not strongly contradictory.

If statistical gates pass, practical $5k implementability is evaluated separately. A positive institutional-style 84-futures portfolio is NOT automatically a retail candidate.

## Anti-overfitting
Do not search other breakout windows after seeing the primary result.
The 1-week / 2-week exit variants mentioned by Murphy are reserved for a new preregistered project only if the primary rule merits continuation.
