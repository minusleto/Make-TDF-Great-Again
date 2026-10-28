---
title: Экономика
description: "Экономические скриптовые эффекты"
head:
  - tag: style
    content: |
      main:has(h1#экономика, h1#economy) .sl-markdown-content > h2:first-child {
        margin-top: 0.5rem;
      }
---


<a id="civilian-transport"></a>
## Производство гражданского транспорта

Эти эффекты добавляют гражданский транспорт: автомобили, самолёты, поезда, вертолёты и корабли. Количество задаётся числом в переменной `stuff_to_add`, например `100` или `200`.

```text
set_temp_variable = { stuff_to_add = 1000 }
add_civilian_auto = yes
add_civilian_planes = yes
add_civilian_trains = yes
add_civilian_helos = yes
add_civilian_ships = yes
```

В зависимости от скоупа транспорт добавляется на склад страны или в соответствующий регион. Если в регионе уже достигнут лимит размещения, излишек отправляется на склад страны.

<a id="basic-effects"></a>
## Базовые эффекты

<a id="treasury"></a>
### Казна

Поменять казну на произвольную сумму:

```
set_temp_variable = { treasury_change = 10.00 }
modify_treasury_effect = yes
```

**Малый расход** — 0.2% ВВП
```
small_expenditure = yes
```

**Средний расход** — 0.4% ВВП
```
medium_expenditure = yes
```

**Крупный расход** — 0.6% ВВП
```
large_expenditure = yes
```

<a id="debt"></a>
### Долги

```
set_temp_variable = { debt_change = 1.0 }
modify_debt_effect = yes
```

<a id="investments"></a>
### Инвестиции

```
set_temp_variable = { int_investment_change = 1.0 }
modify_international_investment_effect = yes
```

<a id="taxes"></a>
### Налоги

**Корпоративный налог**
```
set_temp_variable = { corp_change = 2 }
modify_corporate_tax_rate_effect = yes
```

**Подоходный налог**
```
set_temp_variable = { pop_change = 2 }
modify_population_tax_rate_effect = yes
```

<a id="productivity"></a>
### Производительность

```
set_temp_variable = { temp_productivity_change = 25.0 }
flat_productivity_change_effect = yes
```

<a id="capitalization"></a>
### Капитализация

Изменяет капитализацию страны

```
set_temp_variable = { modify_capitalization = 0.010 }
modify_capitalization_support = yes
```


<a id="base-inflation"></a>
### Базовая инфляция

Изменяет базовую инфляцию страны

```
set_temp_variable = { base_inflation_percent_change = 1.0 }
modify_base_inflation_effect = yes
```


<a id="increasedecrease-economic-growth"></a>
### Экономический рост

Увеличивает или уменьшает текущий экономический цикл страны

```
increase_economic_growth = yes
decrease_economic_growth = yes
increase_two_level_economic_growth = yes
decrease_two_level_economic_growth = yes
depression = yes
recession = yes
stagnation = yes
stable_growth = yes
fast_growth = yes
economic_boom = yes
```

<a id="economic-agreements"></a>
## Экономические соглашения

<a id="setremove-trade-agreement"></a>
### Торговое соглашение

Создаёт или удаляет торговое соглашение

- sender_nation --- страна, отправляющая соглашение
- receiver_nation --- страна, получающая соглашение
- remove_agreement --- необязательный параметр (установить в 1)

```
set_temp_variable = { receiver_nation = RAJ.id }
set_temp_variable = { sender_nation = SIN.id }
set_improved_trade_agreement = yes

```

<a id="setremove-mutual-investment-treaty"></a>
### Взаимный инвестиционный договор

Создаёт или удаляет взаимный инвестиционный договор.

- `sender_nation` — страна, отправляющая соглашение
- `receiver_nation` — страна, получающая соглашение
- `remove_treaty` — необязательный параметр (установить в 1 для отмены)

```
set_temp_variable = { receiver_nation = RAJ.id }
set_temp_variable = { sender_nation = SIN.id }
set_mutual_investment_treaty = yes
```

Для отмены:

```
set_temp_variable = { receiver_nation = RAJ.id }
set_temp_variable = { sender_nation = SIN.id }
set_temp_variable = { remove_treaty = 1 }
set_mutual_investment_treaty = yes
```

Торговое соглашение и взаимный инвестиционный договор можно использовать одновременно.

```
set_temp_variable = { receiver_nation = BRA.id }
set_temp_variable = { sender_nation = POR.id }
set_improved_trade_agreement = yes
set_mutual_investment_treaty = yes
```

<a id="setremove-permanent-investment-targets"></a>
### Постоянные цели инвестиций

Добавляет или удаляет adding_nation из инвестиционного пула другой страны под управлением ИИ

- target_nation --- страна, отправляющая соглашение
- adding_nation --- страна, получающая соглашение
- remove_nation --- необязательный параметр (установить в 1)

```
set_temp_variable = { target_nation = RAJ.id }
set_temp_variable = { adding_nation = SIN.id }
change_permanent_investment_target = yes

```

<a id="other"></a>
## Другое

<a id="guide-on-how-to-do-additional-incomeadditional-expenses"></a>
### Доп. доходы и расходы

```
Шаг 1: перейдите в common/scripted_effects/00_money_system.txt
Шаг 2: найдите calculate_additional_income_rate
Шаг 3: в этом разделе должна быть отмеченная секция Country Specific. Добавьте код туда.
if = {
  limit = { original_tag = TAG  }
  if = {
    limit = { has_idea = whatever }
    set_variable = { whatever_gain = 0.05 }
    add_to_variable = { additional_income_rate = whatever_gain }
  }
}
Шаг 4: перейдите в common/scripted_localization/money_scripted_localization.txt. Место внутри файла особого значения не имеет.
defined_text = {
    name = additional_income_summary_whatever
    text = {
        trigger = { has_idea = whatever }
        localization_key = "whatever_TT" #задаёт для этой сводки текст "$$[?whatever_gain|+3] from §Y$whatever$§!\n"
    }
    text = {
        trigger = { NOT = { has_idea = whatever } }
        localization_key = ""
    }
}
Шаг 5: перейдите в MD_money_l_english.yml (localisation/english). Найдите ADDITIONAL_INCOME_REVENUES_TOOLTIP
Затем в конце (или в любом другом месте внутри) добавьте [additional_income_summary_whatever]
Шаг 6: вернитесь в исходный файл идеи — теперь сумма должна отображаться в модификаторах spirits

**ПРИМЕЧАНИЕ** Отображение переменных не будет работать в этом разделе. Вам нужно создать отдельный тултип, явно описывающий нужное значение, либо добавить локализацию в _desc идеи.

Сделайте это в модификаторах:

modifiers = {
  custom_modifier_tooltip = whatever_TT
}

```

<a id="corruption"></a>
## Коррупция

Запустить один случайный коррупционный ивент (`corruption.1`–`corruption.14`) — не изменение какого-то значения, а просто розыгрыш ивента:

```txt
roll_corruption_event = yes
```

Есть внутренний кулдаун — флаг страны на 60 дней, чтобы ивент не всплывал чаще раза в 2 месяца. Веса ивентов при розыгрыше зависят от идей страны:
- Ивент `corruption.13` (про международных банкиров) выпадает вдвое чаще при идее `international_bankers`.
- Ивент `corruption.14` вообще не может выпасть без идеи `oligarchs`.
