# RUN-M0-S6-STRESS-20260817 — приёмочный протокол

## IDEA → SOURCE → HYPOTHESIS → REQUIREMENT

В первом MODELLED sample отсутствовали `DOWN` и `HIGH`. Вместо настройки порогов
создан отдельный stress-pack. Гипотеза и требования `FQL-S6-STRESS-003` ограничены
механическим покрытием ветвей.

## DESIGN → CODE → TEST

ADR-0012 отделяет stress fixtures от истории. Четыре сценария заданы bps-массивами,
генерируют валидные OHLC и получают SHA-256. Полный набор: 71 тест `OK`;
детерминизм, duplicate ID и невозможная доходность проверены; `compileall` и
`git diff --check` — PASS.

## RUN → RESULT

| Сценарий | Trend-классы | Volatility-классы | Метки |
|---|---|---|---:|
| SCN-DOWN-NORMAL | DOWN | NORMAL | 7 |
| SCN-HIGH-OSCILLATION | DOWN, UP | HIGH | 7 |
| SCN-GAP-DOWN | DOWN, RANGE | HIGH, NORMAL | 7 |
| SCN-REVERSAL | DOWN, UP | HIGH, NORMAL | 7 |

Все `UP/DOWN/RANGE` и `HIGH/NORMAL` покрыты. Result SHA-256
`07f53e1e...bccac`; исторические, performance, PAPER и LIVE claims закрыты.

## CRITIQUE → DECISION → LESSON

Аналитик не трактует искусственные частоты. Архитектор отделяет stress suite от
dataset. Программист не подключает торговый движок. Тестировщик подтвердил все
ветви. Риск-контролёр оставил торговые режимы закрытыми. Критик отмечает, что PASS
получен на специально сконструированных путях.

Решение: `ACCEPT_BRANCH_COVERAGE_ONLY`; M0/S2 не повышать. Доказана полнота ветвей
для зарегистрированных fixtures. Не доказаны рыночная реалистичность, вероятность,
accuracy режимов, доходность или готовность PAPER/LIVE.
