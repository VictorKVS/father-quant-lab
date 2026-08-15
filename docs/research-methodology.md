# Research methodology

## Evidence chain

`SOURCE → DATASET → OBSERVATION → HYPOTHESIS → STRATEGY → TEST → RESULT → REVIEW`

## Required timestamps

Every external event must distinguish:

- `event_time`: when the event occurred;
- `published_at`: when a source published it;
- `available_to_system_at`: when the system could actually use it;
- `revised_at`: when the value was later revised.

This prevents look-ahead bias.

## Dataset types

- `REAL_TRADED`
- `OFFICIAL_REFERENCE`
- `SYNTHETIC_RECONSTRUCTION`
- `MODELLED`

Synthetic pre-euro series must never be represented as actual EUR/USD trading data.

## Minimum validation

- deterministic test;
- transaction costs;
- train/test time separation;
- out-of-sample period;
- comparison with a baseline;
- maximum drawdown;
- failure analysis by market regime.
