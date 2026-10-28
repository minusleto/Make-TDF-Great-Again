---
title: Политика
description: "Политические эффекты и работа с партиями"
---

<a id="vanilla-political-effects"></a>
## Ванильные эффекты

Стандартные эффекты игры, применяются напрямую, без обёртки через `set_temp_variable`.

```
add_political_power = 100
```
Добавить очки политической власти (отрицательное значение — отнять).

```
add_stability = 0.05
```
Добавить стабильность (десятичная дробь, 0.05 = +5%; отрицательное значение — отнять).

```
add_war_support = 0.05
```
Добавить военную поддержку (десятичная дробь, 0.05 = +5%; отрицательное значение — отнять).

<a id="ideology-popularity"></a>
### Популярность идеологий

```
add_popularity = {
    ideology = democratic
    popularity = 0.05
}
```

Меняет популярность указанной идеологии на заданную величину (десятичная дробь, 0.05 = +5%; отрицательное значение уменьшает популярность). В `ideology` указывается тег идеологии. В MDC это 5 групп, переосмысленных под сеттинг:

| Тег | Идеология в MDC |
|---|---|
| `democratic` | Западники |
| `communism` | Реакционеры |
| `neutrality` | Нейтралы |
| `nationalist` | Националисты |
| `fascism` | Салафиты |

Чтобы изменить популярность конкретной партии/субидеологии внутри группы (а не всей идеологии целиком), используйте [`add_relative_party_popularity`](#party-popularity) ниже.

<a id="mdc-political-effects"></a>
## Модовые эффекты MDC

<a id="party-popularity"></a>
### Изменение популярности партии

Назначение: увеличивает популярность конкретной партии (субидеологии) на заданную величину.

Параметры:
- `party_index` — индекс изменяемой партии, 0-23. Вместо номера можно указать `set_party_index_to_ruling_party = yes`, чтобы взять индекс правящей партии автоматически.
- `party_popularity_increase` — на сколько меняется популярность партии, десятичная дробь (2% = 0.02)
- `temp_outlook_increase` — опционально, десятичная дробь (2% = 0.02)

```
set_temp_variable = { party_index = 2 }
set_temp_variable = { party_popularity_increase = 0.10 }
set_temp_variable = { temp_outlook_increase = 0.10 }
add_relative_party_popularity = yes
```

📋 [Список всех партий](../../systems/politics/#subideologies) — полная таблица индексов `party_index` (0–23) со всеми субидеологиями.

_**Изменить популярность правящей идеологии:**_

Назначение: изменяет популярность только правящей идеологии на величину `arg_popularity`

```
set_temp_variable = { arg_popularity = +- }
add_ruling_outlook_popularity = yes
```

_**Добавить партию в коалицию**_

Назначение: лёгкий скрипт, динамически локализующий добавление участников в коалицию.

```
set_temp_variable = { add_col_one = 0-23 }
add_coalition_members_effect = yes
```

_**Убрать партию из коалиции**_

Назначение: лёгкий скрипт, динамически локализующий удаление участников из коалиции.

```
set_temp_variable = { remove_col_one = 0-23 }
remove_coalition_members_effect = yes
```

_**Установить правящую партию через эффект**_

Назначение: устанавливает правящую партию на определённую субидеологию через скриптовый эффект. Отдельно нужно прописать `set_politics`, так как этот параметр нельзя задать через переменную.

Параметры:
- `rul_party_temp` — индекс новой правящей партии, 0-23
- `col_one`, `col_two`, `col_three` — опционально, задают первого/второго/третьего участника коалиции, 0-23
- `change_leader_temp = 1` — опционально, если НЕ нужно менять правящего лидера

Важно: `set_politics` должен идти вторым эффектом — иначе `set_party_name` не обновится корректно.

```
set_temp_variable = { rul_party_temp = 20 }
change_ruling_party_effect = yes
set_politics = {
    ruling_party = nationalist
    elections_allowed = no
}
```

_**Изменение порога выборов:**_

Назначение: изменяет порог выборов (минимальное значение, при котором партия учитывается для коалиций).

```
set_temp_variable = { threshold_change = 0.03 }
modify_election_threshold = yes
```

_**Разрешить/запретить партии**_

Запрещает указанный индекс партии для выборов

```
set_temp_variable = { party_index = 1-24 }
ban_party_scripted_call = yes
```

Разрешает указанный индекс партии для выборов

```
set_temp_variable = { party_index = 1-24 }
unban_party_scripted_call = yes
```

```
set_country_flag = free_allow_parties # Задайте это, если не хотите тратить очки политической власти
set_partyall_allowed = yes # Разрешает все партии
```

```
set_country_flag = free_ban_parties # Задайте это, если не хотите тратить очки политической власти
set_partyall_banned = yes # Запрещает все партии
```

<a id="protests"></a>
## Протесты

### Сила протестов

Изменяет силу протестов. Максимальное значение переменной — 100.

```
set_temp_variable = { protest_strength_change = 10 }
modify_protest_effect = yes
```

### Радикализация протестов

Изменяет радикализацию протестов. Максимальное значение переменной — 10. Значения выше 10 не имеют смысла.

```
set_temp_variable = { protest_radicalisation_change = -10 }
modify_protest_radicalisation_effect = yes
```
