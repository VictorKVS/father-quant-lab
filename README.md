# FATHER Quant Lab

Book-to-Market research laboratory for evidence-based market analysis, backtesting, and paper trading.

## Mission

Turn ideas from algorithmic-trading books into reproducible experiments:

`book → hypothesis → code → backtest → critique → paper trade → knowledge`

The project starts with the history of electronic currency trading from 1992. It uses real market and event data, but does **not** place real-money orders.

## Книжная и научная основа

Проект создаётся как практическая лаборатория по книгам об устройстве рынков,
алгоритмической торговле, финансовой математике, машинном обучении и AI. Мы не
копируем примеры вслепую: каждую идею воспроизводим, проверяем на реальных данных,
ищем ограничения и только после независимой проверки включаем в базу знаний.

Рабочий цикл для каждой главы:

`книга → тезис → гипотеза → воспроизводимый код → тест → контрпример → бэктест → paper trading → карточка знания`

Каждая реализация получает стабильный ID вида `BOOK-AUTHOR-CHAPTER-EXPERIMENT`,
ссылку на источник, версию кода, набор данных, метрики, выявленные ошибки и статус:
`idea`, `reproduced`, `challenged`, `validated`, `rejected` или `golden-pattern`.

### Основной маршрут: Python

| Приоритет | Книга | Что воплощаем в проекте |
|---|---|---|
| 1 | [Yves Hilpisch — Python for Algorithmic Trading](https://www.oreilly.com/library/view/python-for-algorithmic/9781492053347/) | Получение данных, NumPy/pandas, векторный и событийный бэктест, momentum, mean reversion, потоковые данные и paper trading |
| 2 | [Yves Hilpisch — Python for Finance](https://www.oreilly.com/library/view/python-for-finance/9781492024323/) | Финансовые временные ряды, моделирование рисков, Monte Carlo и воспроизводимые исследовательские notebooks |
| 3 | [Jason Strimpel — Python for Algorithmic Trading Cookbook](https://www.oreilly.com/library/view/python-for-algorithmic/9781806662036/) | Современный стек pandas/Polars, Parquet/DuckDB, факторные модели, VectorBT/Zipline и отчёты |
| 4 | [Stefan Jansen — Machine Learning for Algorithmic Trading](https://www.packtpub.com/en-us/product/machine-learning-for-algorithmic-trading-9781839217715) | Признаки из рыночных и альтернативных данных, supervised/unsupervised learning, NLP, проверка и интерпретация моделей |
| 5 | [Marcos López de Prado — Advances in Financial Machine Learning](https://www.wiley.com/en-us/shop/general-finance-investments/advances-in-financial-machine-learning-p-9781119482086) | Защита от переобучения и утечки будущего, финансовая кросс-валидация, разметка событий и оценка стратегии |

Python является главным языком исследований, потому что объединяет загрузку данных,
статистику, ML/AI, notebooks, тестирование и быстрые эксперименты. Критический код не
переносится на другой язык, пока Python-прототип не доказал полезность и корректность.

### Устройство рынка и исполнение

| Книга | Назначение |
|---|---|
| [Larry Harris — Trading and Exchanges](https://global.oup.com/academic/product/trading-and-exchanges-9780195144703) | Участники рынка, виды заявок, ликвидность, спред, устройство торговых площадок и причины поведения цен |
| [Álvaro Cartea, Sebastian Jaimungal, José Penalva — Algorithmic and High-Frequency Trading](https://www.cambridge.org/core/books/algorithmic-and-highfrequency-trading/8A2B7905D1C5A6DF718AFA12A2428D61) | Рыночная микроструктура, оптимальное исполнение, market making и математические модели высокочастотной торговли |

Эти книги используются как противовес «красивым стратегиям»: прибыль в бэктесте
не имеет смысла без моделирования bid/ask, ликвидности, задержки, очереди заявок,
проскальзывания, комиссии и влияния собственной заявки на рынок.

### Машинное обучение, AI и агенты

| Книга | Что исследуем |
|---|---|
| [Yves Hilpisch — Artificial Intelligence in Finance](https://www.oreilly.com/library/view/artificial-intelligence-in/9781492055426/) | Нейронные сети, ML, AI-first finance, бэктест, риск и ограничения AI-стратегий |
| [Yves Hilpisch — Reinforcement Learning for Finance](https://www.oreilly.com/library/view/reinforcement-learning-for/9781098169169/) | Финансовые среды, Deep Q-Learning, динамическое распределение активов и оптимальное исполнение |
| [Ernest P. Chan — Generative AI for Trading and Asset Management](https://www.wiley.com/en-us/generative-ai-for-trading-and-asset-management-p-9781394266975) | Применение генеративного AI и LLM в исследовании рынков и управлении активами с обязательной проверкой результатов |

AI-слой FATHER будет использоваться для:

- извлечения экономических, политических, погодных и регуляторных событий;
- связывания события со странами, валютами, сырьём, компаниями и временными лагами;
- формирования проверяемых гипотез и поиска контрдоказательств;
- чтения книг, документации и исследований с сохранением происхождения утверждений;
- генерации исследовательского кода, тестов и объяснений;
- сравнения вариантов стратегии через A/B-тесты и независимого агента-критика;
- ведения журнала решений и накопления `golden-patterns`.

LLM не считается источником рыночной истины, не предсказывает будущее сама по себе
и не получает прямого права отправлять реальные заявки. Любой AI-вывод проходит
структурную проверку данных, бэктест, out-of-sample тест, риск-гейт и paper trading.

### Реализация на других языках

Python остаётся исследовательским и управляющим слоем. После измерения узких мест
отдельные компоненты могут получить эквивалентные реализации:

| Язык | Роль |
|---|---|
| Python | Данные, исследования, бэктест, ML/AI, оркестрация и отчётность |
| SQL | История котировок, событий, экспериментов, сделок и доказательств |
| C++ | Низкая задержка, стакан, симуляция исполнения и производительный risk engine |
| Rust | Безопасные потоковые сервисы, коннекторы и критические компоненты исполнения |
| Java/Kotlin | Интеграция с корпоративными брокерскими и событийными платформами |
| TypeScript | Исследовательская панель, визуализация и объяснение решений |

Для сравнительной практики отслеживаем Early Access издание [Developing High-Frequency Trading Systems, Second Edition](https://www.packtpub.com/en-br/product/developing-high-frequency-trading-systems-9781806114108), где компоненты HFT рассматриваются на C++, Java, Python и Rust. До выхода окончательной редакции материал имеет статус предварительного источника. Перенос считается успешным только при одинаковых входных данных, торговых правилах и результатах с эталонной Python-версией.

### Правила работы с литературой

1. Сохраняем библиографию и ссылку на легальный источник; книги в репозиторий не копируем.
2. Отделяем авторский пример от нашей модификации и собственного вывода.
3. Код из книги адаптируем к текущим версиям библиотек и покрываем тестами.
4. Повторяем эксперимент на нескольких инструментах и рыночных режимах.
5. Учитываем комиссии, spread, slippage, задержки и доступность данных во времени.
6. Ищем опровергающие примеры и документируем условия, при которых метод ломается.
7. Не повторяем исследование без причины: проверенные решения входят в `knowledge/golden-patterns/`.
8. Неподтверждённые и провалившиеся стратегии сохраняем как отрицательный опыт, а не удаляем.

## M0 — Electronic Market History, 1992–2026

First vertical experiment:

1. Study DEM/USD for 1992–1998.
2. Study EUR/USD from 1999 onward.
3. Use USD/JPY and GBP/USD as control series.
4. Implement a moving-average baseline.
5. Compare results across market regimes.
6. Add commissions, spread, slippage, and strict event timestamps.
7. Run paper trading only after backtest gates pass.

## Полигон роботов

Проект сравнивает не одну «лучшую стратегию», а разнообразные семейства роботов,
контрольные алгоритмы и независимых агентов риска. Общий уровень кандидата равен
самому слабому критическому звену. Доходность не повышает зрелость при плохих
данных, переобучении, нереалистичном исполнении или нарушении risk limits.

- [Модель зрелости L0–L7](docs/maturity-model.md)
- [Каталог торговых роботов и контрольных агентов](docs/robot-catalog.md)
- [Исторические и синтетические сценарии полигона](docs/polygon-scenarios.md)
- [Конфигурация первого турнира](configs/tournaments/m0_first_league.yaml)
- [Политика безопасности оператора](docs/operator-safety.md)

### Запуск контрольной лиги

```bash
python -m father_quant_lab run-controls \
  --data data/samples/eurusd_daily_sample.csv \
  --output reports/generated/m0-controls.json
```

Команда создаёт два связанных файла: полный отчёт `m0-controls.json` и паспорт
доказательств `m0-controls.passport.json`. Паспорт связывает исходную идею, ТЗ,
ADR, код, тесты, среду, хеши данных и отчёта, метрики, ограничения, решение и уроки.

Документация реализации:

- [Техническое задание M0 Control League](docs/specifications/m0-control-league.md)
- [Аналитические схемы](docs/analytical-schemes.md)
- [План независимого тестирования](docs/test-plan.md)
- [ADR-0001: минимальный эталонный движок](docs/adr/0001-reference-engine.md)
- [ADR-0002: исполнение на следующем баре](docs/adr/0002-next-bar-execution.md)
- [ТЗ профессиональной торговой консоли](docs/specifications/trading-console.md)
- [ADR-0003: терминал отделён от торгового ядра](docs/adr/0003-console-boundary.md)
- [Стандарт паспортов и полного цикла доказательств](docs/artifact-passports.md)
- [ТЗ S2: официальный справочный курс ECB](docs/specifications/m0-s2-ecb-reference-data.md)
- [ADR-0004: справочный курс не является торговым баром](docs/adr/0004-reference-rates-are-not-bars.md)

### Официальный справочный ряд ECB

```bash
python -m father_quant_lab fetch-ecb-reference \
  --start 2026-01-01 --end 2026-01-31 \
  --raw-output data/raw/ecb/eurusd-2026-01.raw.csv \
  --output data/processed/ecb/eurusd-2026-01.reference.csv \
  --passport reports/generated/eurusd-2026-01.ecb.passport.json
```

Это официальный дневной reference rate для макроконтекста и проверки provenance,
а не исполнимая цена. Команда не запускает бэктест и сохраняет `backtest_eligible=false`.

### Допуск поставщика торговых данных

```bash
python -m father_quant_lab evaluate-providers \
  --registry configs/data-providers/fx_provider_registry.json \
  --output reports/generated/fx-provider-gate.json
```

Gate закрыт по умолчанию: неизвестная лицензия, storage rights, timestamp semantics,
revision policy или недостаточная история дают `BLOCKED`. Текущий результат — ни
один поставщик ещё не допущен даже к ограниченному ingestion pilot.

- [ТЗ FQL-S2-GATE-002](docs/specifications/m0-s2-provider-admission-gate.md)
- [ADR-0005: fail-closed допуск данных](docs/adr/0005-fail-closed-data-admission.md)

## Safety boundary

- No real-money trading.
- No exchange or broker secrets in Git.
- No strategy is accepted on profit alone.
- Every result must include risk, costs, data lineage, and out-of-sample validation.

## Status

`M0 / S0 — repository skeleton created`
