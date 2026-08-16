# BOT-RULE-101 — карта доказательств

Цепочка: `IDEA → SOURCE → HYPOTHESIS → REQUIREMENT → DESIGN → CODE → TEST → RUN → RESULT → CRITIQUE → DECISION → LESSON`.

- IDEA/SOURCE/HYPOTHESIS: `hypothesis.md` и книжный маршрут README.
- REQUIREMENT: `docs/specifications/m0-s4-moving-average-baseline.md`.
- DESIGN: `docs/adr/0007-moving-average-mechanical-baseline.md`.
- CODE: `src/father_quant_lab/strategies.py`, `src/father_quant_lab/cli.py`.
- TEST: `tests/test_strategies.py`, `tests/test_cli.py`, `tests/test_engine.py`.
- RUN/RESULT: `evidence/runs/RUN-M0-RULE-101-20260816/`.
- CRITIQUE: модельная выборка слишком мала и не является рыночной историей.
- DECISION: принять только как механический baseline; зрелость данных и системы не повышать.
- LESSON: воспроизводимость и отсутствие look-ahead проверяются раньше доходности.

Первый результат отрицательный: доходность `-0.784994%`, максимальная просадка
`0.963359%`, 2 сделки. Робот уступил всем трём торгующим контролям. Подбор параметров
после просмотра результата запрещён; это контрдоказательство сохраняется полностью.
