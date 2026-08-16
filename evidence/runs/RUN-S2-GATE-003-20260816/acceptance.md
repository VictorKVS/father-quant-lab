# RUN-S2-GATE-003-20260816 — приёмочный протокол

## IDEA → SOURCE → HYPOTHESIS → REQUIREMENT

Публичные страницы LSEG, OANDA и Dukascopy используются только как первичный
источник, а не как договор. Гипотеза: одинаковые 15 вопросов и immutable sample
contract не дадут превратить рекламное описание в разрешение на покупку или данные
для бэктеста. Полные требования, альтернативы, критерии и риски зафиксированы в
`docs/specifications/m0-s2-vendor-due-diligence.md`.

## DESIGN → CODE → TEST

ADR-0006 разделяет `READY_FOR_VENDOR_QUERY` и
`ELIGIBLE_FOR_OFFLINE_SAMPLE_REVIEW`. Реализован детерминированный модуль
`vendor_due_diligence.py` и CLI `evaluate-vendor-dossiers`. Добавлены 8 тестов:
неполная анкета, один пропущенный ответ, недоказуемая ссылка, повреждённый SHA-256,
отсутствие публичного источника, duplicate ID, полный синтетический dossier и CLI.

Первый запуск `python -m unittest discover -s tests -v` дал 9 import errors:
локальная среда не установила пакет с `src`-layout. Это сохранённый отрицательный
результат среды, код тестов не ослаблялся. Повтор с `PYTHONPATH=src` прошёл: 33 теста,
`OK`; после проверки паспорта полный набор содержит 34 теста. `compileall` и
`git diff --check` — PASS.

## RUN → RESULT

- Dossier: 3 (LSEG, OANDA, Dukascopy).
- `READY_FOR_VENDOR_QUERY`: 3.
- `ELIGIBLE_FOR_OFFLINE_SAMPLE_REVIEW`: 0.
- У каждого 15 незакрытых вопросов и отсутствует immutable sample.
- `purchase_authorized=false`, `credential_use_authorized=false`,
  `trading_data_admitted=false`, `live_orders_forbidden=true`.

Полный машинный результат находится в `result.json`; dossier и результат связаны
SHA-256 в `passport.json`.

## CRITIQUE → DECISION → LESSON

Положительный синтетический тест доказывает достижимость состояния, но ничего не
доказывает о реальном поставщике. Статус `READY_FOR_VENDOR_QUERY` не подтверждает
качество бренда: он означает лишь, что у кандидата есть HTTPS-основание и готов
единый список вопросов. Sample может быть выборочно лучше основной поставки, поэтому
даже успешная проверка не допускает dataset автоматически.

Решение по артефакту: `ACCEPTED`; по данным: `BLOCKED`. Следующий шаг требует внешнего
контакта и не выполняется автоматом. Пока ответы не получены, безопасный технический
рубеж — реализовать валидатор качества только для синтетического sample contract.
