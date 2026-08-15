# FATHER Quant Lab

Book-to-Market research laboratory for evidence-based market analysis, backtesting, and paper trading.

## Mission

Turn ideas from algorithmic-trading books into reproducible experiments:

`book → hypothesis → code → backtest → critique → paper trade → knowledge`

The project starts with the history of electronic currency trading from 1992. It uses real market and event data, but does **not** place real-money orders.

## M0 — Electronic Market History, 1992–2026

First vertical experiment:

1. Study DEM/USD for 1992–1998.
2. Study EUR/USD from 1999 onward.
3. Use USD/JPY and GBP/USD as control series.
4. Implement a moving-average baseline.
5. Compare results across market regimes.
6. Add commissions, spread, slippage, and strict event timestamps.
7. Run paper trading only after backtest gates pass.

## Safety boundary

- No real-money trading.
- No exchange or broker secrets in Git.
- No strategy is accepted on profit alone.
- Every result must include risk, costs, data lineage, and out-of-sample validation.

## Status

`M0 / S0 — repository skeleton created`
