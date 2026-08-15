# Аналитические схемы M0

## Разделение ответственности

```mermaid
flowchart TD
    A["Analyst: ТЗ и гипотеза"] --> D["Data contract"]
    D --> P["Programmer: reference engine"]
    P --> T["Tester: independent checks"]
    T --> C{"Gate passed?"}
    C -->|No| A
    C -->|Yes| R["Evidence report"]
```

Аналитик не подтверждает собственный код. Программист не меняет критерии приёмки
после получения результата. Тестировщик проверяет не прибыль, а соответствие ТЗ,
причинность времени, риск и воспроизводимость.

## Временная причинность

```mermaid
sequenceDiagram
    participant M as Market bar
    participant S as Strategy
    participant R as Risk Guardian
    participant E as Execution model
    participant J as Evidence journal
    M->>S: Close bar N
    S->>R: Target for N+1
    R->>E: Approved target
    E->>E: Wait for open N+1
    E->>J: Fill with costs
```

Стратегия получает только историю до текущего закрытия. Цена открытия следующего
бара становится доступна лишь при исполнении и не участвует в формировании сигнала.

## Контур одного запуска

```mermaid
flowchart TD
    C["Versioned CSV"] --> V["Strict validation"]
    V --> B["Bars in UTC"]
    B --> S["Control strategy"]
    S --> G["Risk Guardian"]
    G --> X["Next-bar execution"]
    X --> M["Equity and drawdown"]
    M --> K{"Kill switch?"}
    K -->|Continue| S
    K -->|Stop| L["Liquidate virtually"]
    L --> J["JSON evidence"]
    M --> J
```

## Сравнение роботов

Все роботы используют один dataset, initial equity, cost model, risk policy и период.
Меняется только стратегия. Это позволяет отличить ценность сигнала от различий в
риске, комиссиях или доступных данных.
