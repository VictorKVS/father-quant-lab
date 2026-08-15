# Каталог роботов и агентов

## Два контура

Полигон разделяет торговых роботов, которые предлагают виртуальные действия, и
контрольных агентов, которые обеспечивают данные, риск, критику и доказательность.
Стратегия не может сама подтвердить собственную безопасность.

## Обязательные контрольные роботы

| ID | Робот | Назначение |
|---|---|---|
| BOT-CTRL-000 | NO-TRADE | Нулевая доходность и нулевой рыночный риск; проверка, что торговля вообще оправдана |
| BOT-CTRL-001 | RANDOM | Случайные сигналы с тем же бюджетом риска; контроль ложной закономерности |
| BOT-CTRL-002 | BUY-HOLD | Простое удержание базового актива или валютной позиции |
| BOT-CTRL-003 | PERIODIC | Периодическая ребалансировка без прогнозирования |

## Правиловые стратегии

| ID | Класс | Примеры вариантов |
|---|---|---|
| BOT-RULE-101 | Trend following | SMA/EMA crossover, time-series momentum, multi-timeframe trend |
| BOT-RULE-102 | Breakout | Donchian, volatility breakout, range breakout |
| BOT-RULE-103 | Mean reversion | Z-score, Bollinger, RSI reversion |
| BOT-RULE-104 | Carry | Процентный дифференциал и стоимость переноса для валют |
| BOT-RULE-105 | Pairs/stat-arb | Cointegration, spread reversion, basket residual |
| BOT-RULE-106 | Volatility | Volatility targeting, volatility regime switch |
| BOT-RULE-107 | Grid | Сетка только в ограниченном диапазоне с жёстким stop regime |
| BOT-RULE-108 | Market making | Spread quoting, inventory control, Avellaneda–Stoikov variant |

## Событийные и фундаментальные стратегии

| ID | Класс | Сигналы |
|---|---|---|
| BOT-EVENT-201 | Central bank | Ставки, guidance, сюрприз относительно ожиданий |
| BOT-EVENT-202 | Macro surprise | Инфляция, занятость, ВВП, пересмотры показателей |
| BOT-EVENT-203 | Political/geopolitical | Выборы, санкции, конфликты, торговые ограничения |
| BOT-EVENT-204 | Weather/supply | Ураганы, засухи, порты, добыча, энергетическая инфраструктура |
| BOT-EVENT-205 | Regulatory | Правила для банков, брокеров, криптоактивов и капитала |
| BOT-EVENT-206 | Cross-asset chain | Событие → сырьё → инфляция → ставка → валюта |

## ML/AI-роботы

| ID | Класс | Ограничение |
|---|---|---|
| BOT-ML-301 | Supervised classifier | Вероятность режима или направления; обязательная calibration |
| BOT-ML-302 | Return/risk forecaster | Прогноз распределения, а не одна точка |
| BOT-ML-303 | NLP event model | Извлекает событие и уверенность; не торгует напрямую |
| BOT-ML-304 | Regime detector | Выбирает допустимые семейства стратегий |
| BOT-ML-305 | Reinforcement learning | Только отдельная среда с реалистичными friction и строгим out-of-sample |
| BOT-AI-306 | LLM research agent | Формирует гипотезы, код и контрдоказательства; заявки запрещены |
| BOT-AI-307 | Ensemble/meta-controller | Распределяет виртуальный риск между прошедшими gate роботами |

## Контрольные агенты FATHER

| ID | Агент | Полномочие |
|---|---|---|
| AGT-DATA-401 | Data Sentinel | Блокирует эксперимент при плохом качестве или неизвестном происхождении данных |
| AGT-TIME-402 | Time Auditor | Ищет look-ahead, неверные timezone, публикации и revisions |
| AGT-RISK-403 | Risk Guardian | Ограничивает позицию, leverage, drawdown и включает kill switch |
| AGT-EXEC-404 | Execution Simulator | Моделирует spread, latency, fills, fees и market impact |
| AGT-CRITIC-405 | Principal Critic | Ищет переобучение, неверную причинность и недоказанные выводы |
| AGT-RED-406 | Adversarial Tester | Портит поток данных, задерживает сообщения и создаёт экстремальные режимы |
| AGT-LIB-407 | Evidence Librarian | Ведёт lineage книг, данных, гипотез, тестов и выводов |
| AGT-COUNCIL-408 | Engineering Council | Выдаёт решение `promote`, `hold`, `reject` или `retest` |

## Первый состав полигона

Первый турнир ограничен двенадцатью участниками:

1. четыре контрольных робота;
2. trend following;
3. breakout;
4. mean reversion;
5. pairs/stat-arb;
6. volatility targeting;
7. macro-event robot;
8. regime detector + rule-based strategy;
9. простой ML classifier.

Grid, market making, RL и LLM-meta-controller допускаются только после готовности
стакана, модели исполнения и критических измерений не ниже L3.

## Кандидаты движков

| Движок | Роль на полигоне |
|---|---|
| [VectorBT](https://vectorbt.dev/) | Быстрые массовые parameter sweeps и первичная проверка идей |
| [Backtrader](https://www.backtrader.com/docu/) | Совместимость с книжными примерами и событийные учебные тесты |
| [NautilusTrader](https://nautilustrader.io/docs/latest/concepts/overview/) | Предпочтительный кандидат для детального event-driven backtest и sandbox; Python + Rust |
| [LEAN](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine) | Независимая кросс-проверка на Python/C# и альтернативных моделях исполнения |
| [Freqtrade](https://www.freqtrade.io/en/stable/backtesting/) | Крипто-бэктест, hyperopt и dry-run после появления криптоконтура |
| [Hummingbot](https://hummingbot.org/client/global-configs/paper-trade/) | Paper market making и тестирование биржевых сценариев без активов |
| [FinRL](https://finrl.readthedocs.io/en/latest/start/introduction.html) | Изолированные и воспроизводимые эксперименты reinforcement learning |

Ни один внешний движок не является источником истины. Важные стратегии повторяются
на собственном минимальном эталонном движке и хотя бы одном независимом движке.
