# FQL-SPEC-M0-S2 — официальный справочный курс EUR/USD

## Идея и гипотеза

До проверки торговых стратегий система должна доказать, что умеет получать данные
из официального источника, сохранять сырой ответ, происхождение и ограничения.

Гипотеза: адаптер может воспроизводимо принять официальный дневной справочный курс
ECB `EXR.D.USD.EUR.SP00.A`, не выдавая его за доступную торговую цену или OHLC-бар.

## Источник

- Издатель: European Central Bank.
- Набор: Exchange Rates (`EXR`).
- Ряд: `EXR.D.USD.EUR.SP00.A` — US dollar/Euro ECB reference exchange rate, Daily.
- API: `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A`.

## Требования

| ID | Требование | Проверка |
|---|---|---|
| FQL-S2-FR-001 | URL жёстко ограничен официальным HTTPS endpoint и рядом | `test_url_is_fixed_to_official_series_and_bounded_dates` |
| FQL-S2-FR-002 | Сырой ответ сохраняется до преобразования | CLI `--raw-output` |
| FQL-S2-FR-003 | Принимаются только ожидаемые series/currency/denominator | `test_rejects_wrong_series_and_unordered_dates` |
| FQL-S2-FR-004 | Даты уникальны и возрастают, значения положительны | `test_reference_data.py` |
| FQL-S2-FR-005 | Паспорт содержит URL, время получения, SHA-256 raw/canonical | `test_passport_blocks_reference_rate_from_backtest` |
| FQL-S2-FR-006 | Reference rate технически несовместим с OHLC loader | `test_passport_blocks_reference_rate_from_backtest` |

## Альтернативы

1. Превратить reference rate в `open=high=low=close`. Отклонено: создаёт фиктивную
   исполнимую свечу и скрывает отсутствие bid/ask, high/low и времени доступности.
2. Сразу подключить брокера. Отклонено: требует договора, ключей, юридической и
   финансовой границы; для S2 это неоправданный риск.
3. Использовать неофициальный бесплатный агрегатор. Отложено: проще технически, но
   слабее происхождение и неизвестны редакции/лицензия.

## Критерии приёмки

- parser и negative tests зелёные без сети;
- raw и canonical имеют отдельные SHA-256;
- паспорт содержит `backtest_eligible=false`;
- ни один путь адаптера не вызывает `BacktestEngine`;
- реальный сетевой прогон остаётся отдельным evidence и не подменяется fixture.

## Риски и границы доказанности

Адаптер доказывает ingestion и lineage, но не качество торговых котировок, точное
время публикации, отсутствие последующих исправлений, возможность исполнения,
доходность стратегии или готовность live-контура.
