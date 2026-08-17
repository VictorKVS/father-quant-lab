# План тестирования M0 Control League

## Роли

### Программист

- реализует только зарегистрированные требования;
- предоставляет детерминированные интерфейсы;
- документирует допущения в ADR;
- не ослабляет тест ради зелёного результата.

### Тестировщик

- строит проверки от требований, а не от внутреннего устройства кода;
- атакует временную причинность, данные, издержки и risk boundary;
- сохраняет найденный дефект как воспроизводимый тест;
- выдаёт `PASS`, `FAIL` или `BLOCKED` с доказательством.

## Наборы тестов

| Набор | Содержание |
|---|---|
| DATA | timezone, OHLC, порядок, дубликаты, смешанные инструменты и CSV-schema |
| TIME | сигнал N → исполнение N+1, отсутствие будущих цен |
| EXEC | spread, slippage, commission, финальная ликвидация |
| RISK | short/leverage rejection, max drawdown, kill switch, no re-entry |
| CTRL | NO-TRADE, RANDOM reproducibility, BUY-HOLD и PERIODIC |
| REPORT | JSON schema, стабильный порядок, запрет live orders |
| CLI | запуск одной командой и повторяемый файл |
| SUFF | отдельный warm-up каждого split, minimum scored bars и fail-closed criteria |
| REGIME | warm-up, фиксированные пороги, timestamp доступности и неизменность от будущего бара |
| ATTR | dataset hash, timestamps, warm-up coverage и запрет использования меток стратегией |
| STRESS | deterministic fixtures, branch coverage, unique IDs и запрет исторических claims |

## Definition of Done

- тесты стандартной библиотеки проходят без сети;
- CLI выполнен дважды, отчёты идентичны;
- `git diff --check` чист;
- sample не выдается за реальный исторический dataset;
- открытые ограничения перечислены в итоговом отчёте.
