---
title: Военные
description: "Скриптовые триггеры войны: пограничные конфликты, доктрины, сопротивление, ядерное оружие, медали, НАТО."
---

## Пограничные конфликты

```
is_border_conflict_defender_vs_FROM = yes
```
Проверяет, что у текущей страны выставлена переменная `defender_state_vs_@FROM` — то есть она обороняющаяся сторона в пограничном конфликте против страны `FROM`.

| Триггер | Проверяет |
|---|---|
| `has_not_initiated_border_incident_with_FROM` | Ни один штат страны не отмечен как «защищаемый от FROM» (инцидент не инициирован против FROM) |
| `has_not_initiated_border_incident_with_ROOT` | То же самое, но относительно ROOT |
| `has_ROOT_at_least_1_div_in_current_state_scope` | У ROOT есть хотя бы 1 дивизия в текущем штате (scope — штат) |
| `is_rojava` | `original_tag = ROJ` |
| `is_turkey` | `original_tag = TUR` |

## Военные доктрины

`does_not_have_*_doctrine` — проверяют **отсутствие** конкретной ветки доктрин (базовой и «улучшенной/dedicated» версии сразу):

| Триггер | Доктрины (любая из них = условие ложно) |
|---|---|
| `does_not_have_deep_battle_doctrine` | `deep_battle`, `dedicated_deep_battle` |
| `does_not_have_supply_doctrine` | `decentralized_supply_theory`, `centralized_supply_theory`, `scavenging_supply_theory` |
| `does_not_have_volunteer_force` | `volunteer_fighting_force`, `dedicated_volunteer_fighting_force` |
| `does_not_have_thunder_run_doctrine` | `thunder_run`, `dedicated_thunder_run` |
| `does_not_have_light_infantry_warfare_doctrine` | `light_infantry_warfare`, `dedicated_light_infantry_warfare` |
| `does_not_have_guerrilla_fighters_doctrine`¹ | `guerrilla_fighters`, `dedicated_guerrilla_fighters` |
| `does_not_have_static_defense_doctrine` | `static_defense`, `dedicated_static_defense` |
| `does_not_have_elastic_defense_doctrine` | `elastic_defense`, `dedicated_elastic_defense` |
| `does_not_have_mobile_defense_doctrine` | `mobile_defense`, `dedicated_mobile_defense` |
| `does_not_have_insurgent_operations_doctrine`¹ | `insurgent_operations`, `dedicated_insurgent_operations` |

¹ У этих двух в исходнике внутри `NOT` дополнительно требуется наличие доктрины `guerrilla_warfare` — то есть они истинны, только если страна **вообще выбрала** ветку герильи, но не взяла именно этот узел.

## Сопротивление

```
should_initiate_resistance = yes
```
Определяет, должно ли в штате быть сопротивление: `check_variable = { core_countries^num > 0 }` (есть чьи-то ещё коренные претензии на штат) **И НЕ** `is_core_of = FROM` (штат не является кором оккупанта).

Можно переопределить для конкретных штатов, дав триггеру имя `should_initiate_resistance_<state_id>` или сразу для нескольких `should_initiate_resistance_<id1>_<id2>_<id3>` — движок сам подхватит именно эту версию вместо общей, если она существует (пример есть закомментированным прямо в исходнике для Германии).

```
should_activate_active_crypto_bonuses = yes
should_not_activate_active_crypto_bonuses = yes
```
Хуки для переопределения решения ИИ о включении бонусов взломанной крипто-связи (используются при взломе шифров другой страны). По умолчанию оба `always = no` — то есть готового поведения нет, это точки расширения на будущее, а не рабочая логика прямо сейчас.

## Ядерное оружие

| Триггер | Проверяет |
|---|---|
| `check_if_nuclear_weapons_in_stockpile` | Есть на складе `nuclear_missile_equipment` или `nuclear_ballistic_missile_equipment` больше временного порога |
| `is_able_to_use_nuclear_strikes` | Ядерная доктрина позволяет удар: `full_first_use`, либо страну уже когда-то «наносили» (`has_country_flag = has_been_nuked`) при доктринах retaliation-типа |
| `is_able_to_use_nuclear_strikes_tac` | То же самое, но для тактического удара конкретно (без `strategic_retaliation_only`) |
| `ai_is_able_to_use_nuclear_strikes_tac` | Версия для ИИ: либо страна не под ИИ, либо (под ИИ) высокий threat + началась 4-я эпоха + (высокий прогресс капитуляции цели ИЛИ невыгодное соотношение сил) |
| `is_able_to_launch_a_nuclear_strike` | Оборонительная доктрина (`nuclear_power_def`) и цель — свой/заявленный штат с прогрессом капитуляции > 50%, ИЛИ доктрина `nuclear_power_off` (без ограничений) |

## Гуманитарный коридор

```
humanitarian_corridor_avaliable = yes
```
(да, в исходнике опечатка `avaliable`, а не `available` — имя нужно копировать буквально). Проверяет, что у целевого штата уже 4-й уровень модификатора «продуктивность зависимых территорий» и что есть соседний штат — как под контролем ROOT, так и под контролем FROM — без ещё более высоких уровней (5–8) этого же модификатора, то есть коридор ещё имеет смысл прокладывать.

## НАТО

```
NATO_currently_exists = yes
```
Проверяет, что глобальный массив `nato_members` не пуст (нулевой элемент массива ≠ 0).

## Медали за дивизии

Два параллельных набора — ванильный (`00_unit_medals_scripted_triggers.txt`) и MDC-специфичный (`MD_unit_medals_scripted_triggers.txt`), который **не является расширением** первого, а полностью самостоятельный список со своей логикой:

| Страна | Ванильный | MDC |
|---|---|---|
| Германия | `should_have_german_medals_trigger` | `MD_should_have_german_medals_trigger` |
| США | `should_have_usa_medals_trigger` | `MD_should_have_usa_medals_trigger` |
| СССР/Россия | `should_have_soviet_medals_trigger` | `MD_should_have_soviet_medals_trigger`¹ / `MD_should_have_russian_medals_trigger`² |
| Британия | `should_have_english_medals_trigger` | `MD_should_have_english_medals_trigger` |
| Франция | `should_have_french_medals_trigger` | `MD_should_have_french_medals_trigger` |
| Италия | `should_have_italian_medals_trigger` | `MD_should_have_italian_medals_trigger` |
| Япония | `should_have_japanese_medals_trigger` | `MD_should_have_japanese_medals_trigger` |
| Эфиопия | `should_have_ethiopian_medals_trigger` | — |
| Китай | — | `MD_should_have_chinese_medals_trigger` |
| Иран | — | `MD_should_have_iranian_medals_trigger` |
| Вагнер (ЧВК) | — | `MD_should_have_wagner_medals_trigger`³ |
| Голландия | — | учтена только внутри `MD_should_have_any_unique_medals_trigger` (`original_tag = HOL`), отдельного именованного триггера нет |

¹ Советские медали в MDC-версии выдаются только если у власти формирующиеся коммунисты (`emerging_communist_state_are_in_power`).
² Российские медали (новое имя вместо «советских») — России, но только если у власти **не** военная хунта (`nationalist_military_junta_are_in_power`).
³ Вагнер получает медали либо если страна и есть `WAG`, либо если это Россия под властью военной хунты — то есть один и тот же режим (хунта) переключает страну между «российскими» и «вагнеровскими» медалями в зависимости от того, чей это тег.

```
should_have_any_unique_medals_trigger = yes       # ванильная версия
MD_should_have_any_unique_medals_trigger = yes    # MDC-версия
```
Сводный `OR` по всем строкам таблицы выше — «есть ли у страны вообще уникальный набор медалей».
