# Product passport

## Product

- ID: `FQL-PROD-0001`
- Name: FATHER Quant Lab
- Type: educational and research system
- Mode: backtesting and paper trading only

## Goal

Create a reproducible laboratory that tests book-derived trading hypotheses against real market and event data across historical market regimes.

## Initial scope

- Electronic trading history: 1992–2026
- Instruments: DEM/USD, EUR/USD, USD/JPY, GBP/USD
- Crypto extension: BTC/USD after the currency pipeline is stable
- Baseline strategy: moving-average crossover
- Required costs: spread, commission, slippage

## Acceptance gate for M0

The first milestone is complete when one command can load a versioned sample, run a deterministic backtest, produce risk metrics, and save an auditable report without accessing a live trading account.
